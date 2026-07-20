"""설정 파일이 정상적으로 로드되고 원본 데이터 경로가 실제로 존재하는지 확인합니다."""

from __future__ import annotations

import pytest

from fablens.utils.config import load_features, load_paths, load_split, resolve


def test_paths_config_loads():
    paths = load_paths()
    for section in ("raw", "interim", "processed", "reports", "artifacts"):
        assert section in paths, f"paths.yaml에 '{section}' 섹션이 없습니다"


def test_raw_data_exists():
    """원본 데이터가 로컬에 있는지 확인합니다.

    .gitignore가 raw CSV를 제외하므로 clone 직후에는 실패할 수 있습니다.
    그 경우 데이터 배포 절차를 먼저 수행해야 합니다.
    """
    paths = load_paths()
    trace_dir = resolve(paths["raw"]["trace_dir"])
    removal_rate = resolve(paths["raw"]["removal_rate"])

    if not trace_dir.is_dir():
        pytest.skip(f"원본 데이터 없음: {trace_dir}")

    traces = sorted(trace_dir.glob(paths["raw"]["trace_glob"]))
    assert len(traces) == 185, f"trace CSV가 185개가 아닙니다: {len(traces)}개"
    assert removal_rate.is_file(), f"라벨 파일 없음: {removal_rate}"


def test_features_config_structure():
    features = load_features()
    assert features["target"] == "AVG_REMOVAL_RATE"
    assert features["keys"]["wafer_id"] == "WAFER_ID"
    assert features["keys"]["stage"] == "STAGE"
    assert features["sensor_candidates"], "센서 후보가 비어 있습니다"


def test_split_config_ratios_sum_to_one():
    split = load_split()
    ratios = split["ratios"]
    total = ratios["train"] + ratios["validation"] + ratios["test"]
    assert abs(total - 1.0) < 1e-9, f"split 비율 합이 1이 아닙니다: {total}"
    assert split["method"] == "chronological"
