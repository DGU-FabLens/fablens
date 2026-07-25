"""Feature Table 생성 로직 검증 (TD-003, 데이터 계약 §4).

원본 없이 합성 trace로 순수 함수를 테스트합니다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from fablens.features.build import (
    apply_exclusions,
    build_feature_table,
    classify_chamber,
    remove_target_outliers,
)

# 최소 config (sensor 2개, 집계 전체)
FEATS = {
    "keys": {"wafer_id": "WAFER_ID", "stage": "STAGE"},
    "target": "AVG_REMOVAL_RATE",
    "time_column": "TIMESTAMP",
    "sensor_candidates": {"g": ["S1", "S2"]},
    "aggregations": ["mean", "std", "min", "max", "range", "slope", "delta"],
    "derived": {"process_time": True, "n_samples": True, "prev_wafer_diff": True},
    "target_outliers": {"rule": "AVG_REMOVAL_RATE > 1000"},
    "exclusion_rules": {"drop_constant": True, "constant_threshold": 1, "correlation_threshold": 0.95},
}


def _traces() -> pd.DataFrame:
    """2개 wafer-stage. S1은 시간에 선형 증가, S2는 상수."""
    rows = []
    for wid, chamber in [(1, 1), (2, 4)]:
        for t in range(5):
            rows.append(
                {
                    "WAFER_ID": wid,
                    "STAGE": "A",
                    "TIMESTAMP": float(t),
                    "CHAMBER": float(chamber),
                    "S1": float(t * 2 + wid),  # slope=2, delta=8
                    "S2": 7.0,                 # 상수
                }
            )
    return pd.DataFrame(rows)


def _labels() -> pd.DataFrame:
    return pd.DataFrame(
        {"WAFER_ID": [1, 2], "STAGE": ["A", "A"], "AVG_REMOVAL_RATE": [80.0, 90.0]}
    )


def test_classify_chamber():
    assert classify_chamber(frozenset({1, 2, 3})) == "G123"
    assert classify_chamber(frozenset({4, 5})) == "G456"
    assert classify_chamber(frozenset({3, 4})) == "MIXED"
    assert classify_chamber(frozenset()) == "UNKNOWN"


def test_build_shape_and_keys():
    table, skipped = build_feature_table(_traces(), _labels(), FEATS)
    assert len(table) == 2
    assert table.duplicated(["WAFER_ID", "STAGE"]).sum() == 0
    assert "chamber_group" in table.columns
    assert set(table["chamber_group"]) == {"G123", "G456"}
    # process_time = 4 (t 0..4), n_samples = 5
    assert (table["process_time"] == 4).all()
    assert (table["n_samples"] == 5).all()
    # prev_wafer_diff는 미구현으로 skipped에 보고
    assert "prev_wafer_diff" in skipped


def test_slope_and_delta_values():
    table, _ = build_feature_table(_traces(), _labels(), FEATS)
    # S1 slope=2, delta = 마지막-첫 = (4*2)-(0*2) = 8
    assert np.allclose(table["S1_slope"], 2.0)
    assert np.allclose(table["S1_delta"], 8.0)
    assert np.allclose(table["S1_range"], 8.0)  # max-min = (8+wid)-(0+wid)=8


def test_target_outlier_removal():
    table, _ = build_feature_table(_traces(), _labels(), FEATS)
    table.loc[0, "AVG_REMOVAL_RATE"] = 5000.0  # 이상치 주입
    kept, n = remove_target_outliers(table, FEATS)
    assert n == 1
    assert len(kept) == 1


def test_exclusions_drop_constant_and_correlated():
    table, _ = build_feature_table(_traces(), _labels(), FEATS)
    feature_cols = [
        c for c in table.columns
        if c not in {"WAFER_ID", "STAGE", "chamber_group", "first_ts", "last_ts", "order_index", "AVG_REMOVAL_RATE"}
    ]
    kept, rep = apply_exclusions(table, feature_cols, FEATS)
    # S2는 상수(mean/min/max 동일, std=0, range=0) → 상당수 제거되어야 함
    assert rep["n_dropped_constant"] >= 1
    assert rep["n_kept"] < rep["n_input"]
