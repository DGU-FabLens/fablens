"""wafer-stage Feature Table 생성 (TD-003, 데이터 계약 §4).

2주차 산출물. VM 모델(선형/RF/XGBoost)의 입력 테이블과 스키마를 만듭니다.

실행::

    .venv/bin/python scripts/03_build_features.py

산출물::

    data/processed/feature_table.parquet    wafer-stage 1건 = 1행
    data/processed/feature_schema.json       강민수 쪽이 컬럼명 대신 읽는 스키마
"""

from __future__ import annotations

import json
import sys
from io import StringIO

import pandas as pd

from fablens.data.raw import load_traces
from fablens.features.build import (
    apply_exclusions,
    build_feature_table,
    remove_target_outliers,
)
from fablens.utils.config import load_features, load_paths, resolve

# 데이터 계약 §2 기준값
EXPECTED_BEFORE = 1981
EXPECTED_AFTER = 1977

META_COLUMNS = ["first_ts", "last_ts", "order_index"]


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
    keys = [feats["keys"]["wafer_id"], feats["keys"]["stage"]]
    target = feats["target"]

    print("=== [1] 원본 로딩 ===")
    traces = load_traces(resolve(paths["raw"]["trace_dir"]), paths["raw"]["trace_glob"])
    labels = pd.read_csv(resolve(paths["raw"]["removal_rate"]))
    print(f"  trace row: {len(traces):,} / 라벨: {len(labels):,}")

    print("\n=== [2] wafer-stage 집계 ===")
    table, skipped = build_feature_table(traces, labels, feats)
    print(f"  wafer-stage: {len(table):,}")
    if len(table) != EXPECTED_BEFORE:
        print(f"  [경고] 기대값 {EXPECTED_BEFORE}와 다릅니다.")
    if skipped:
        print(f"  [미구현 파생 feature] {skipped} → 계산 정의 확정 후 추가 예정")

    # 타깃 결측(라벨 누락) 확인
    n_missing_target = int(table[target].isna().sum())
    print(f"  타깃 결측(Join 누락): {n_missing_target}건")

    print("\n=== [3] 타깃 이상치 제거 ===")
    table, n_removed = remove_target_outliers(table, feats)
    print(f"  제거 {n_removed}건 → {len(table):,}건 (기대 {EXPECTED_AFTER})")
    if len(table) != EXPECTED_AFTER:
        print(f"  [경고] 기대값 {EXPECTED_AFTER}와 다릅니다. 원인 확인 필요.")

    # feature 후보 = 전체 컬럼 - (key/meta/조건/타깃)
    non_feature = set(keys + META_COLUMNS + ["chamber_group", target])
    feature_cols = [c for c in table.columns if c not in non_feature]

    print("\n=== [4] 제외 규칙 적용 (상수·고상관) ===")
    kept, rep = apply_exclusions(table, feature_cols, feats)
    print(f"  입력 {rep['n_input']} → 상수 제거 {rep['n_dropped_constant']}"
          f" → 고상관 제거 {rep['n_dropped_correlated']} → 최종 {rep['n_kept']}")
    if rep["dropped_constant"]:
        print(f"  상수: {rep['dropped_constant']}")
    if rep["n_kept"] > 60:
        print(f"  [주의] 최종 feature {rep['n_kept']}개 > TD-003 목표 60개. 추가 축소 검토.")
    elif rep["n_kept"] < 30:
        print(f"  [주의] 최종 feature {rep['n_kept']}개 < TD-003 목표 30개.")

    # 최종 테이블: key + 조건 + meta + target + 최종 feature
    ordered_cols = keys + ["chamber_group"] + META_COLUMNS + [target] + kept
    final = table[ordered_cols].copy()

    # --- 불변 조건 ---
    assert final.duplicated(keys).sum() == 0, "동일 wafer-stage 중복"
    assert final[kept].isna().sum().sum() == 0, "feature에 결측 존재"

    print("\n=== [5] 조건별 타깃 분포 (sanity) ===")
    print(final.groupby(["STAGE", "chamber_group"])[target].describe()[["count", "mean", "std"]].round(2).to_string())

    # 저장
    proc_root = resolve(paths["processed"]["root"])
    proc_root.mkdir(parents=True, exist_ok=True)
    ft_path = resolve(paths["processed"]["feature_table"])
    final.to_parquet(ft_path, index=False)

    schema = {
        "n_rows": len(final),
        "keys": keys,
        "meta_columns": META_COLUMNS,
        "condition_columns": ["STAGE", "chamber_group"],
        "target": target,
        "feature_columns": kept,
        "n_features": len(kept),
    }
    schema_path = proc_root / "feature_schema.json"
    schema_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")

    sys.stdout = sys.__stdout__
    print(f"\n산출물 저장:\n  {ft_path}\n  {schema_path}")
    print(f"  최종: {len(final):,}행 × feature {len(kept)}개")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
