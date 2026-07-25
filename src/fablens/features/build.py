"""wafer-stage Feature Table 생성 (TD-003, 데이터 계약 §4).

원본 trace(672,744 row)를 wafer-stage(1,981건) 단위 통계 집계로 바꿔 VM 모델
입력 테이블을 만듭니다. 센서·집계함수·제외규칙은 하드코딩하지 않고
``config/features.yaml``에서 읽습니다.

집계 정의:
  mean/std/min/max : 그룹 내 통계
  range            : max - min
  slope            : TIMESTAMP에 대한 1차 회귀 기울기 (시간 추세)
  delta            : 시간순 마지막값 - 첫값

Feature 컬럼명은 ``{원본컬럼}_{집계함수}`` (데이터 계약 §3). SHAP에서 센서를
역추적해야 하므로 원본 컬럼명을 축약하지 않습니다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# config/features.yaml 의 chamber_group 정의 (DL-20260720-002)
_G123, _G456 = frozenset({1, 2, 3}), frozenset({4, 5, 6})


def classify_chamber(values: frozenset) -> str:
    """wafer-stage 안에서 관측된 CHAMBER 값 집합을 그룹으로 분류합니다."""
    if not values:
        return "UNKNOWN"
    if values <= _G123:
        return "G123"
    if values <= _G456:
        return "G456"
    return "MIXED"


def sensor_columns(feats: dict) -> list[str]:
    """config의 sensor_candidates를 평평한 센서 컬럼 리스트로 폅니다."""
    cols: list[str] = []
    for group in feats["sensor_candidates"].values():
        cols.extend(group)
    return cols


def _basic_aggregations(
    traces: pd.DataFrame, keys: list[str], sensors: list[str], aggs: list[str]
) -> pd.DataFrame:
    """mean/std/min/max/range 를 groupby로 한 번에 계산합니다."""
    base = [a for a in ("mean", "std", "min", "max") if a in aggs]
    need = base or ["mean"]  # range 계산에 min/max가 필요할 수 있음
    if "range" in aggs:
        need = list(dict.fromkeys(need + ["min", "max"]))

    g = traces.groupby(keys)[sensors].agg(need)
    # MultiIndex 컬럼 (sensor, agg) → "sensor_agg"
    g.columns = [f"{s}_{a}" for s, a in g.columns]

    out = pd.DataFrame(index=g.index)
    for s in sensors:
        for a in base:
            out[f"{s}_{a}"] = g[f"{s}_{a}"]
        if "range" in aggs:
            out[f"{s}_range"] = g[f"{s}_max"] - g[f"{s}_min"]
    return out.reset_index()


def _slope_delta(
    traces: pd.DataFrame,
    keys: list[str],
    sensors: list[str],
    time_column: str,
    aggs: list[str],
) -> pd.DataFrame:
    """slope(시간 회귀 기울기)와 delta(마지막-첫값)를 그룹별로 계산합니다.

    traces는 (keys, time_column) 오름차순 정렬을 전제로 합니다.
    slope는 그룹마다 센서 전체를 한 번의 선형대수로 계산합니다.
    """
    want_slope, want_delta = "slope" in aggs, "delta" in aggs
    if not (want_slope or want_delta):
        return pd.DataFrame({k: [] for k in keys})

    rows = []
    for key_vals, grp in traces.groupby(keys, sort=False):
        rec = dict(zip(keys, key_vals if isinstance(key_vals, tuple) else (key_vals,)))
        x = grp[sensors].to_numpy(dtype=float)  # (n, k)
        if want_slope:
            t = grp[time_column].to_numpy(dtype=float)
            tc = t - t.mean()
            denom = (tc * tc).sum()
            if denom == 0:
                slopes = np.zeros(x.shape[1])
            else:
                slopes = (tc[:, None] * (x - x.mean(axis=0))).sum(axis=0) / denom
            for s, v in zip(sensors, slopes):
                rec[f"{s}_slope"] = v
        if want_delta:
            deltas = x[-1] - x[0]
            for s, v in zip(sensors, deltas):
                rec[f"{s}_delta"] = v
        rows.append(rec)
    return pd.DataFrame(rows)


def _derived_features(
    traces: pd.DataFrame, keys: list[str], time_column: str, derived: dict
) -> pd.DataFrame:
    """process_time, n_samples 등 그룹 단위 파생 feature.

    prev_wafer_diff / chamber_dwell_time 은 계산 정의가 아직 확정되지 않아
    이 버전에서는 구현하지 않고 호출부에서 경고를 남깁니다.
    """
    g = traces.groupby(keys)
    out = pd.DataFrame(index=g.size().index)
    if derived.get("process_time"):
        ts = g[time_column]
        out["process_time"] = ts.max() - ts.min()
    if derived.get("n_samples"):
        out["n_samples"] = g.size()
    return out.reset_index()


def build_feature_table(
    traces: pd.DataFrame,
    labels: pd.DataFrame,
    feats: dict,
) -> tuple[pd.DataFrame, list[str]]:
    """Feature Table과 미구현 파생 feature 목록을 반환합니다.

    Args:
        traces: 원본 trace concat.
        labels: (WAFER_ID, STAGE, AVG_REMOVAL_RATE) 라벨.
        feats: ``config/features.yaml`` dict.

    Returns:
        (feature_table, skipped_derived)
        feature_table 은 이상치 제거·제외규칙 적용 전의 원시 집계 결과입니다.
        제외규칙은 ``apply_exclusions``에서 별도로 적용합니다.
    """
    keys = [feats["keys"]["wafer_id"], feats["keys"]["stage"]]
    target = feats["target"]
    time_column = feats["time_column"]
    sensors = sensor_columns(feats)
    aggs = feats["aggregations"]

    traces = traces.sort_values([*keys, time_column], kind="stable")

    basic = _basic_aggregations(traces, keys, sensors, aggs)
    slopedelta = _slope_delta(traces, keys, sensors, time_column, aggs)
    derived = _derived_features(traces, keys, time_column, feats.get("derived", {}))

    # 그룹 타이밍 + chamber_group 조건 변수
    ts = traces.groupby(keys)[time_column]
    meta = pd.DataFrame({"first_ts": ts.min(), "last_ts": ts.max()}).reset_index()
    chamber_sets = traces.groupby(keys)["CHAMBER"].apply(
        lambda s: frozenset(int(v) for v in s.dropna().unique())
    )
    meta["chamber_group"] = [classify_chamber(chamber_sets[k]) for k in chamber_sets.index]

    table = meta
    for part in (basic, slopedelta, derived):
        table = table.merge(part, on=keys, how="left")
    table = table.merge(labels[keys + [target]], on=keys, how="left")

    # order_index: first_ts 시간순 순번 (split manifest와 동일 정렬 기준)
    table = table.sort_values("first_ts", kind="stable").reset_index(drop=True)
    table["order_index"] = range(len(table))

    # 아직 구현하지 않은 파생 feature 확인
    skipped = [
        name
        for name in ("prev_wafer_diff", "chamber_dwell_time")
        if feats.get("derived", {}).get(name)
    ]
    return table, skipped


def remove_target_outliers(table: pd.DataFrame, feats: dict) -> tuple[pd.DataFrame, int]:
    """타깃 이상치 규칙(예: AVG_REMOVAL_RATE > 1000)을 적용합니다 (DL-20260720-003)."""
    rule = feats["target_outliers"]["rule"]
    before = len(table)
    kept = table.query(f"not ({rule})").reset_index(drop=True)
    return kept, before - len(kept)


def apply_exclusions(
    table: pd.DataFrame, feature_cols: list[str], feats: dict
) -> tuple[list[str], dict]:
    """상수·고상관 feature를 제거하고 최종 feature 목록을 돌려줍니다.

    Returns:
        (kept_features, report) — report는 제거 내역 dict.
    """
    rules = feats.get("exclusion_rules", {})
    dropped_constant: list[str] = []
    dropped_correlated: list[dict] = []

    cols = list(feature_cols)

    if rules.get("drop_constant"):
        thr = rules.get("constant_threshold", 1)
        dropped_constant = [c for c in cols if table[c].nunique(dropna=True) <= thr]
        cols = [c for c in cols if c not in dropped_constant]

    corr_thr = rules.get("correlation_threshold")
    if corr_thr is not None and len(cols) > 1:
        corr = table[cols].corr().abs()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        for col in list(upper.columns):
            partners = upper.index[upper[col] > corr_thr].tolist()
            if partners and col in cols:
                cols.remove(col)
                dropped_correlated.append({"dropped": col, "corr_with": partners[0]})

    report = {
        "n_input": len(feature_cols),
        "n_dropped_constant": len(dropped_constant),
        "dropped_constant": dropped_constant,
        "n_dropped_correlated": len(dropped_correlated),
        "dropped_correlated": dropped_correlated,
        "n_kept": len(cols),
    }
    return cols, report
