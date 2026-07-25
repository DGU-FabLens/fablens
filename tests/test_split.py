"""Split 로직의 불변 조건을 검증합니다 (TD-002, 데이터 계약 §5).

원본 데이터 없이 합성 wafer-stage 타이밍으로 순수 함수를 테스트합니다.
"""

from __future__ import annotations

import pandas as pd

from fablens.data.split import (
    BUFFER,
    TEST,
    TRAIN,
    VALIDATION,
    assign_order,
    assign_segments,
    build_manifest,
)

RATIOS = {"train": 0.6, "validation": 0.2, "test": 0.2}


def _timing(n: int, overlap: bool = False) -> pd.DataFrame:
    """겹치지 않는(또는 경계에서 겹치는) 합성 wafer-stage 타이밍 n건."""
    # train/validation 경계 직전 인덱스. 여기 샘플의 last_ts를 길게 늘려
    # 경계를 넘어 validation 구간과 겹치게 만든다.
    boundary_i = round(n * RATIOS["train"]) - 1
    rows = []
    for i in range(n):
        first = float(i * 100)
        last = first + (350 if overlap and i == boundary_i else 10)
        rows.append({"WAFER_ID": 1000 + i, "STAGE": "A", "first_ts": first, "last_ts": last})
    return pd.DataFrame(rows)


def _split_cfg(margin: float = 0, buffer_enabled: bool = True) -> dict:
    return {
        "method": "chronological",
        "order_by": "first_ts",
        "ratios": RATIOS,
        "boundary_buffer": {"enabled": buffer_enabled, "extra_margin_sec": margin},
        "manifest_columns": ["WAFER_ID", "STAGE", "first_ts", "order_index", "split"],
    }


def test_assign_order_is_chronological():
    ws = _timing(10).sample(frac=1, random_state=0)  # 뒤섞어도
    ordered = assign_order(ws, "first_ts")
    assert list(ordered["order_index"]) == list(range(10))
    assert ordered["first_ts"].is_monotonic_increasing


def test_segments_ratio_and_time_order():
    ws = assign_order(_timing(100), "first_ts")
    seg = assign_segments(ws, RATIOS)
    assert (seg == TRAIN).sum() == 60
    assert (seg == VALIDATION).sum() == 20
    assert (seg == TEST).sum() == 20
    # train의 모든 first_ts < validation의 모든 first_ts < test
    assert ws.loc[seg == TRAIN, "first_ts"].max() < ws.loc[seg == VALIDATION, "first_ts"].min()
    assert ws.loc[seg == VALIDATION, "first_ts"].max() < ws.loc[seg == TEST, "first_ts"].min()


def test_each_wafer_stage_appears_once():
    ws = _timing(50)
    manifest = build_manifest(ws, _split_cfg())
    assert manifest.duplicated(["WAFER_ID", "STAGE"]).sum() == 0
    assert len(manifest) == 50


def test_split_values_are_valid():
    manifest = build_manifest(_timing(50), _split_cfg())
    assert set(manifest["split"]) <= {TRAIN, VALIDATION, TEST, BUFFER}


def test_no_buffer_when_no_overlap():
    manifest = build_manifest(_timing(100, overlap=False), _split_cfg())
    assert (manifest["split"] == BUFFER).sum() == 0


def test_overlap_produces_buffer():
    # 경계에서 겹치도록 만든 뒤 buffer가 생기는지 확인
    manifest = build_manifest(_timing(100, overlap=True), _split_cfg())
    assert (manifest["split"] == BUFFER).sum() >= 1


def test_buffer_disabled_keeps_all_used():
    manifest = build_manifest(_timing(100, overlap=True), _split_cfg(buffer_enabled=False))
    assert (manifest["split"] == BUFFER).sum() == 0
