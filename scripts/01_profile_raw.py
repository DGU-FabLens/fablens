"""원본 데이터 프로파일링 및 Join 정합성 검증.

1주차 필수 산출물입니다. 결과 숫자는 이후 전처리·Feature 단계의 기준값이 됩니다.
전처리를 하지 않고 **확인만** 합니다.

실행::

    .venv/bin/python scripts/01_profile_raw.py

산출물::

    reports/data_profile/wafer_stage_profile.csv   wafer-stage별 요약
    reports/data_profile/column_profile.csv        컬럼별 결측/고유값
    reports/data_profile/summary.txt               콘솔 출력 전문
"""

from __future__ import annotations

import sys
from io import StringIO

import pandas as pd

from fablens.utils.config import load_features, load_paths, resolve

KEY = ["WAFER_ID", "STAGE"]


def load_traces(trace_dir, glob_pattern: str) -> pd.DataFrame:
    """185개 trace CSV를 하나로 합칩니다.

    파일 1개가 웨이퍼 1개가 아니므로, 파일명은 식별자로 사용하지 않고
    `source_file`은 추적용으로만 남깁니다.
    """
    files = sorted(trace_dir.glob(glob_pattern))
    if not files:
        raise FileNotFoundError(f"trace CSV를 찾을 수 없습니다: {trace_dir}/{glob_pattern}")

    frames = []
    empty_files = []
    for f in files:
        df = pd.read_csv(f)
        if df.empty:
            empty_files.append(f.name)
            continue
        df["source_file"] = f.name
        frames.append(df)

    print(f"trace 파일 {len(files)}개 중 {len(frames)}개 로드, 빈 파일 {len(empty_files)}개")
    if empty_files:
        print(f"  빈 파일: {', '.join(empty_files)}")
    return pd.concat(frames, ignore_index=True)


def profile_columns(tr: pd.DataFrame) -> pd.DataFrame:
    """컬럼별 결측/고유값/상수 여부를 정리합니다."""
    rows = []
    for col in tr.columns:
        s = tr[col]
        rows.append(
            {
                "column": col,
                "dtype": str(s.dtype),
                "n_missing": int(s.isna().sum()),
                "pct_missing": round(s.isna().mean() * 100, 3),
                "n_unique": int(s.nunique(dropna=True)),
                "is_constant": bool(s.nunique(dropna=True) <= 1),
            }
        )
    return pd.DataFrame(rows)


def build_wafer_stage(tr: pd.DataFrame) -> pd.DataFrame:
    """wafer-stage 단위로 집계합니다 (TD-001)."""
    g = (
        tr.groupby(KEY)
        .agg(
            n_rows=("TIMESTAMP", "size"),
            first_ts=("TIMESTAMP", "min"),
            last_ts=("TIMESTAMP", "max"),
            n_chamber=("CHAMBER", "nunique"),
            n_machine=("MACHINE_ID", "nunique"),
            n_source_file=("source_file", "nunique"),
        )
        .reset_index()
    )
    g["duration"] = g["last_ts"] - g["first_ts"]

    # CHAMBER 계열 판정 (DL-20260720-002)
    chamber_sets = tr.groupby(KEY)["CHAMBER"].apply(
        lambda s: frozenset(int(v) for v in s.dropna().unique())
    )
    g["chamber_group"] = (
        g.set_index(KEY)
        .index.map(lambda k: classify_chamber(chamber_sets.get(k, frozenset())))
        .to_numpy()
    )
    return g


def classify_chamber(values: frozenset) -> str:
    """CHAMBER 값 집합을 G123 / G456 으로 분류합니다."""
    if not values:
        return "UNKNOWN"
    if values <= {1, 2, 3}:
        return "G123"
    if values <= {4, 5, 6}:
        return "G456"
    return "MIXED"


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

    tr = load_traces(resolve(paths["raw"]["trace_dir"]), paths["raw"]["trace_glob"])
    lab = pd.read_csv(resolve(paths["raw"]["removal_rate"]))

    print(f"\n총 row: {len(tr):,}")
    print(f"라벨 row: {len(lab):,}")

    print("\n=== [1] 컬럼 프로파일 ===")
    colprof = profile_columns(tr)
    print(colprof.to_string(index=False))
    constants = colprof.loc[colprof.is_constant, "column"].tolist()
    print(f"\n상수 컬럼(모델 feature 제외 대상): {constants or '없음'}")

    print("\n=== [2] wafer-stage 집계 ===")
    ws = build_wafer_stage(tr)
    print(f"고유 wafer-stage: {len(ws):,}")
    print(f"라벨 중복 (WAFER_ID, STAGE): {lab.duplicated(KEY).sum()}")

    print("\n=== [3] Join 정합성 ===")
    m = ws.merge(lab, on=KEY, how="outer", indicator=True)
    counts = m["_merge"].value_counts()
    print(counts.to_string())
    n_missing_label = int(counts.get("left_only", 0))
    n_missing_trace = int(counts.get("right_only", 0))
    print(f"센서만 있고 라벨 없음: {n_missing_label}건")
    print(f"라벨만 있고 센서 없음: {n_missing_trace}건")

    both = m[m["_merge"] == "both"].drop(columns="_merge").copy()

    print("\n=== [4] STAGE / CHAMBER 계열별 타깃 분포 ===")
    print(
        both.groupby(["STAGE", "chamber_group"])["AVG_REMOVAL_RATE"]
        .describe()
        .round(2)
        .to_string()
    )

    print("\n=== [5] 타깃 이상치 ===")
    rule = feats["target_outliers"]["rule"]
    expected = feats["target_outliers"]["expected_removed"]
    outliers = both.query(rule)
    print(f"규칙: {rule}  (기대 건수 {expected})")
    print(
        outliers[KEY + ["chamber_group", "n_rows", "duration", "AVG_REMOVAL_RATE"]]
        .sort_values("AVG_REMOVAL_RATE", ascending=False)
        .to_string(index=False)
    )
    print(f"실제 제외 대상: {len(outliers)}건")
    if len(outliers) != expected:
        print(f"  [경고] 기대 건수 {expected}와 다릅니다. 원인 확인이 필요합니다.")

    print("\n=== [6] 그룹 단위 이상치 후보 (미처리) ===")
    print(both.groupby("STAGE")[["n_rows", "duration"]].describe().round(1).T.to_string())
    print(
        "\nCHAMBER가 그룹 안에서 변하는 wafer-stage: "
        f"{(both.n_chamber > 1).sum()}건 / {len(both)}건"
    )
    print(f"CHAMBER 계열 분포:\n{both.chamber_group.value_counts().to_string()}")

    out_dir = resolve(paths["reports"]["data_profile"])
    out_dir.mkdir(parents=True, exist_ok=True)
    both.to_csv(out_dir / "wafer_stage_profile.csv", index=False)
    colprof.to_csv(out_dir / "column_profile.csv", index=False)

    sys.stdout = sys.__stdout__
    (out_dir / "summary.txt").write_text(buf.getvalue(), encoding="utf-8")
    print(f"\n산출물 저장: {out_dir}")

    # Join 누락이 있으면 실패로 처리해 다음 단계 진입을 막습니다.
    return 1 if (n_missing_label or n_missing_trace) else 0


if __name__ == "__main__":
    raise SystemExit(main())
