"""시간순 train/validation/test 분할과 경계 buffer 판정 (TD-002).

원칙 (config/split.yaml):
  - wafer-stage를 ``first_ts`` 오름차순으로 정렬해 시간순으로 나눕니다.
  - 동일 wafer-stage는 반드시 하나의 split에만 속합니다 (TD-001).
  - 멀티 챔버 장비라 경계에서 여러 웨이퍼의 처리 구간이 겹칩니다.
    경계를 넘어 시간이 겹치는 샘플은 ``split='buffer'``로 표시해 학습·평가
    어디에도 쓰지 않습니다 (DL-20260720-005).

이 모듈은 순수 함수만 두어 테스트 가능하게 하고, 파일 입출력은
``scripts/02_build_split.py``가 담당합니다.
"""

from __future__ import annotations

import pandas as pd

# split 컬럼이 가질 수 있는 값
TRAIN, VALIDATION, TEST, BUFFER = "train", "validation", "test", "buffer"

# 시간순으로 인접한 (앞 구간, 뒤 구간) 경계 목록
_BOUNDARIES = [(TRAIN, VALIDATION), (VALIDATION, TEST)]


def assign_order(ws: pd.DataFrame, order_by: str) -> pd.DataFrame:
    """``order_by`` 오름차순으로 정렬해 ``order_index``(0부터)를 붙입니다.

    first_ts 중복은 원본에서 0건으로 확인되어 순서가 유일하게 정해지지만,
    재현성을 위해 동률일 때 key로 안정 정렬합니다.
    """
    keys = [c for c in ("WAFER_ID", "STAGE") if c in ws.columns]
    ordered = ws.sort_values([order_by, *keys], kind="stable").reset_index(drop=True)
    ordered["order_index"] = range(len(ordered))
    return ordered


def assign_segments(ws: pd.DataFrame, ratios: dict[str, float]) -> pd.Series:
    """order_index 기준으로 train/validation/test 구간을 count 비율로 나눕니다.

    경계 buffer를 적용하기 **전**의 1차 구간입니다. 반환값은 ``ws`` 행 순서에
    맞춘 segment Series입니다.
    """
    n = len(ws)
    n_train = round(n * ratios[TRAIN])
    n_val = round(n * ratios[VALIDATION])
    # test는 나머지. 경계 인덱스가 뒤집히지 않도록 방어합니다.
    n_train = min(n_train, n)
    n_val = min(n_val, n - n_train)

    idx = ws["order_index"].to_numpy()
    seg = pd.Series(TEST, index=ws.index, dtype=object)
    seg[idx < n_train] = TRAIN
    seg[(idx >= n_train) & (idx < n_train + n_val)] = VALIDATION
    return seg


def flag_boundary_buffer(
    ws: pd.DataFrame,
    segment: pd.Series,
    extra_margin_sec: float = 0.0,
) -> pd.Series:
    """경계에서 시간이 겹치는 뒤 구간 샘플을 buffer로 바꿉니다.

    판정 방식 (DL-20260720-005, config/split.yaml ``boundary_buffer``):
    앞 구간 L에서 처리 구간이 가장 늦게 끝나는 시각 ``max(last_ts)``보다
    ``first_ts``가 이른 뒤 구간 R의 샘플은, 시간상 L과 겹치므로 buffer로
    분류합니다. ``extra_margin_sec``는 buffer 폭을 넓히는 추가 여유입니다.

    앞 구간 L은 buffer 적용 후 실제로 남는 샘플만으로 경계를 계산합니다
    (앞 경계에서 buffer가 된 샘플은 다음 경계 계산에서 제외).
    """
    split = segment.copy()
    for left, right in _BOUNDARIES:
        left_end = ws.loc[split == left, "last_ts"].max()
        if pd.isna(left_end):
            continue
        overlaps = (split == right) & (ws["first_ts"] < left_end + extra_margin_sec)
        split[overlaps] = BUFFER
    return split


def build_manifest(ws_timing: pd.DataFrame, split_cfg: dict) -> pd.DataFrame:
    """wafer-stage 타이밍 표에서 Split Manifest를 생성합니다.

    Args:
        ws_timing: ``WAFER_ID, STAGE, first_ts, last_ts`` 를 포함한 표
            (``fablens.data.raw.wafer_stage_timing`` 출력).
        split_cfg: ``config/split.yaml`` 로 로드한 dict.

    Returns:
        데이터 계약 §5 스키마의 manifest DataFrame. 컬럼 순서는
        ``manifest_columns`` 설정을 따르며, 내부 계산용 ``last_ts`` 등은
        진단을 위해 뒤에 함께 반환합니다(호출부에서 필요한 컬럼만 저장).
    """
    if split_cfg.get("method") != "chronological":
        raise ValueError(f"지원하지 않는 split method: {split_cfg.get('method')}")

    ws = assign_order(ws_timing, split_cfg["order_by"])
    segment = assign_segments(ws, split_cfg["ratios"])

    buffer_cfg = split_cfg.get("boundary_buffer", {})
    if buffer_cfg.get("enabled", False):
        margin = float(buffer_cfg.get("extra_margin_sec", 0) or 0)
        ws["split"] = flag_boundary_buffer(ws, segment, margin)
    else:
        ws["split"] = segment

    return ws
