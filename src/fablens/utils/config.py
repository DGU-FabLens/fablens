"""설정 파일 로더.

경로와 설정값을 코드에 하드코딩하지 않기 위한 모듈입니다
(02_AI_DEVELOPMENT_RULES 9장).

사용 예::

    from fablens.utils.config import load_paths, resolve

    paths = load_paths()
    trace_dir = resolve(paths["raw"]["trace_dir"])
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONFIG_DIRNAME = "config"


def repo_root() -> Path:
    """저장소 루트를 반환합니다.

    이 파일은 `<root>/src/fablens/utils/config.py`에 위치하므로
    상위 3단계가 루트입니다.
    """
    return Path(__file__).resolve().parents[3]


def config_dir() -> Path:
    return repo_root() / CONFIG_DIRNAME


def load_config(name: str) -> dict[str, Any]:
    """`config/<name>.yaml`을 읽어 dict로 반환합니다.

    Args:
        name: 확장자를 제외한 설정 파일 이름. 예: ``"paths"``.

    Raises:
        FileNotFoundError: 설정 파일이 없는 경우.
    """
    path = config_dir() / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")
    with path.open(encoding="utf-8") as f:
        loaded = yaml.safe_load(f)
    return loaded or {}


def load_paths() -> dict[str, Any]:
    return load_config("paths")


def load_features() -> dict[str, Any]:
    return load_config("features")


def load_split() -> dict[str, Any]:
    return load_config("split")


def resolve(relative_path: str) -> Path:
    """설정에 기록된 저장소 루트 기준 상대 경로를 절대 경로로 바꿉니다."""
    return repo_root() / relative_path
