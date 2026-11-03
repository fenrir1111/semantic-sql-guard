from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "data" / "registry.yaml"


@pytest.fixture
def registry():
    from semantic_sql_guard.semantic.registry import load_registry

    return load_registry(REGISTRY_PATH)


@pytest.fixture
def pipeline(registry, tmp_path):
    from semantic_sql_guard.pipeline import Pipeline

    return Pipeline(
        registry,
        f"sqlite:///{tmp_path / 'test.db'}",
        str(tmp_path / "audit.log"),
    )
