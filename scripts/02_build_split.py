"""시간순 Split Manifest 생성 (TD-002, 데이터 계약 §5).

2주차 산출물의 첫 단계입니다. Feature Table보다 먼저 만들어 강민수(SPC)에게
넘기면 Phase I 경계 작업이 병렬로 시작됩니다.

실행::

    .venv/bin/python scripts/02_build_split.py

산출물::

    data/processed/split_manifest.csv   wafer-stage별 train/validation/test/buffer

이 스크립트는 경계 buffer 폭(config/split.yaml ``extra_margin_sec``, 현재 0)을
확정하는 데 필요한 **중첩 분포**를 함께 출력합니다. 숫자를 보고 강민수와
extra_margin_sec / Phase I 구간(데이터 계약 §7)을 합의합니다.
"""

from __future__ import annotations

import sys
from io import StringIO

import pandas as pd

from fablens.data.raw import load_traces, wafer_stage_timing
from fablens.data.split import (
    BUFFER,
    TEST,
    TRAIN,
    VALIDATION,
    assign_segments,
    build_manifest,
)
from fablens.utils.config import load_features, load_paths, load_split, resolve

# 데이터 계약 §2의 검증 기준값
EXPECTED_WAFER_STAGE = 1981
USED_SPLITS = [TRAIN, VALIDATION, TEST]


def print_diagnostics(ws: pd.DataFrame) -> None:
    """구간 크기와 경계 중첩 분포를 출력합니다."""
    print("\n=== [2] Split 구간 분포 ===")
    counts = ws["split"].value_counts()
    total = len(ws)
    for name in [TRAIN, VALIDATION, TEST, BUFFER]:
        n = int(counts.get(name, 0))
        print(f"  {name:<11}: {n:>5}건 ({n / total * 100:5.1f}%)")
    print(f"  {'합계':<11}: {total:>5}건")

    used = ws[ws["split"].isin(USED_SPLITS)]
    print(f"\n  학습·평가 사용(train+val+test): {len(used):,}건")
    print(f"  buffer 제외: {int(counts.get(BUFFER, 0)):,}건")

    print("\n=== [3] 구간별 first_ts 범위 (시간순 분리 확인) ===")
    for name in USED_SPLITS:
        seg = ws.loc[ws["split"] == name, "first_ts"]
        if not seg.empty:
            print(f"  {name:<11}: first_ts [{seg.min():,.0f} ~ {seg.max():,.0f}]")

    print("\n=== [4] 경계 중첩 분포 (extra_margin_sec 확정 근거) ===")
    # 각 buffer 샘플을 buffer 적용 '전' 원래 구간으로 귀속시켜 경계별로 집계합니다.
    orig_segment = assign_segments(ws, load_split()["ratios"])
    for left, right in [(TRAIN, VALIDATION), (VALIDATION, TEST)]:
        # 이 경계에서 앞 구간(left)의 실제 종료 시각
        left_end = ws.loc[ws["split"] == left, "last_ts"].max()
        # 원래 right 구간이었으나 buffer가 된 샘플 = 이 경계 때문에 겹친 샘플
        caused = ws[(orig_segment == right) & (ws["split"] == BUFFER)]
        overlap = (left_end - caused["first_ts"]).dropna()
        print(f"  {left} → {right}: 앞 구간 last_ts_max={left_end:,.0f}")
        if overlap.empty:
            print("    겹치는 buffer 샘플 없음")
        else:
            print(
                f"    buffer {len(overlap)}건, 중첩 길이(초) "
                f"min={overlap.min():,.0f} / 중앙값={overlap.median():,.0f} / "
                f"max={overlap.max():,.0f}"
            )

    print("\n=== [5] 구간별 최장 처리시간 (긴 꼬리 확인) ===")
    for name in USED_SPLITS:
        seg = ws.loc[ws["split"] == name, "duration"]
        if not seg.empty:
            print(f"  {name:<11}: duration max={seg.max():,.0f}초, 중앙값={seg.median():,.0f}초")


def main() -> int:
    buf = StringIO()

    class Tee:
        def write(self, s):
            sys.__stdout__.write(s)
            buf.write(s)

        def flush(self):
            sys.__stdout__.flush()

    sys.stdout = Tee()

    paths = load_paths()
    feats = load_features()
    split_cfg = load_split()

    keys = [feats["keys"]["wafer_id"], feats["keys"]["stage"]]
    time_col = feats["time_column"]

    print("=== [1] wafer-stage 타이밍 집계 ===")
    traces = load_traces(resolve(paths["raw"]["trace_dir"]), paths["raw"]["trace_glob"])
    ws_timing = wafer_stage_timing(traces, keys, time_col)
    print(f"  고유 wafer-stage: {len(ws_timing):,}")
    if len(ws_timing) != EXPECTED_WAFER_STAGE:
        print(f"  [경고] 기대값 {EXPECTED_WAFER_STAGE}와 다릅니다. 원본을 확인하세요.")
    dup = ws_timing.duplicated(["first_ts"]).sum()
    print(f"  first_ts 중복: {dup}건 (0이어야 정렬이 유일)")

    manifest = build_manifest(ws_timing, split_cfg)
    print_diagnostics(manifest)

    # --- 불변 조건 검증 ---
    assert manifest.duplicated(keys).sum() == 0, "동일 wafer-stage가 중복 등장합니다"
    assert set(manifest["split"]) <= {TRAIN, VALIDATION, TEST, BUFFER}, "알 수 없는 split 값"

    out_cols = split_cfg["manifest_columns"]
    out = manifest[out_cols].copy()
    out_path = resolve(paths["processed"]["split_manifest"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    sys.stdout = sys.__stdout__
    print(f"\n산출물 저장: {out_path}")
    print(f"  컬럼: {list(out.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
