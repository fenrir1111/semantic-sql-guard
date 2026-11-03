"""从 registry.yaml 加载语义注册表。"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import yaml

from .models import Metric, Registry, RowPermission, Term


def load_registry(path: Union[str, Path]) -> Registry:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    metrics: dict[str, Metric] = {}
    for m in raw.get("metrics", []):
        metric = Metric(
            id=m["id"],
            name=m["name"],
            aliases=list(m.get("aliases", [])),
            table=m["table"],
            measure=m["measure"],
            agg=str(m.get("agg", "SUM")).upper(),
            dim_columns=list(m.get("dim_columns", [])),
            sensitive=bool(m.get("sensitive", False)),
            max_value=m.get("max_value"),
            description=m.get("description", ""),
        )
        metrics[metric.id] = metric

    terms = [
        Term(word=t["word"], column=t["column"], value=str(t["value"]))
        for t in raw.get("terms", [])
    ]

    rp_raw = raw.get("row_permission")
    row_permission = (
        RowPermission(column=rp_raw["column"], role_values=rp_raw["role_values"])
        if rp_raw
        else None
    )

    return Registry(
        metrics=metrics,
        terms=terms,
        sensitive_tables=set(raw.get("sensitive_tables", [])),
        sensitive_allowed_roles=set(raw.get("sensitive_allowed_roles", [])),
        row_permission=row_permission,
    )


def save_registry(registry: Registry, path: Union[str, Path]) -> None:
    """把注册表序列化回 registry.yaml（供可视化后台编辑持久化）。"""
    data = {
        "metrics": [
            {
                "id": m.id,
                "name": m.name,
                "aliases": m.aliases,
                "table": m.table,
                "measure": m.measure,
                "agg": m.agg,
                "dim_columns": m.dim_columns,
                "sensitive": m.sensitive,
                **({"max_value": m.max_value} if m.max_value is not None else {}),
                **({"description": m.description} if m.description else {}),
            }
            for m in registry.metrics.values()
        ],
        "terms": [{"word": t.word, "column": t.column, "value": t.value} for t in registry.terms],
        "sensitive_tables": sorted(registry.sensitive_tables),
        "sensitive_allowed_roles": sorted(registry.sensitive_allowed_roles),
        "row_permission": (
            {
                "column": registry.row_permission.column,
                "role_values": registry.row_permission.role_values,
            }
            if registry.row_permission
            else None
        ),
    }
    Path(path).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
