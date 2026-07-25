"""원본 trace 로딩과 wafer-stage 타이밍 집계.

전처리 결과가 아니라 **원본에서 계산 가능한 최소 정보**만 다룹니다.
Split Manifest(TD-002)와 이후 Feature Table이 공통으로 쓰는 wafer-stage
경계 시각(first_ts / last_ts)을 여기서 한 곳에 정의합니다.

경로·컬럼명은 하드코딩하지 않고 config에서 읽습니다
(02_AI_DEVELOPMENT_RULES 9장).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_traces(trace_dir: Path, glob_pattern: str) -> pd.DataFrame:
    """trace CSV들을 하나로 합칩니다.

    파일 1개가 웨이퍼 1개가 아니므로 파일명은 식별자로 쓰지 않고
    ``source_file``은 추적용으로만 남깁니다. 빈 파일(헤더 전용)은 건너뜁니다.
    """
    files = sorted(trace_dir.glob(glob_pattern))
    if not files:
        raise FileNotFoundError(f"trace CSV를 찾을 수 없습니다: {trace_dir}/{glob_pattern}")

    frames = []
    for f in files:
        df = pd.read_csv(f)
        if df.empty:
            continue
        df["source_file"] = f.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def wafer_stage_timing(
    traces: pd.DataFrame,
    keys: list[str],
    time_column: str,
) -> pd.DataFrame:
    """wafer-stage 단위 시간 경계를 계산합니다 (TD-001).

    Returns:
        컬럼 ``keys + [n_rows, first_ts, last_ts, duration]`` 인 DataFrame.
        ``first_ts``는 그룹 최초 TIMESTAMP, ``last_ts``는 최후 TIMESTAMP입니다.
        TIMESTAMP는 절대 시각이 아니라 순서용 float이므로 정렬·경계 판정에만
        사용합니다 (config/features.yaml 참조).
    """
    g = (
        traces.groupby(keys)
        .agg(
            n_rows=(time_column, "size"),
            first_ts=(time_column, "min"),
            last_ts=(time_column, "max"),
        )
        .reset_index()
    )
    g["duration"] = g["last_ts"] - g["first_ts"]
    return g
