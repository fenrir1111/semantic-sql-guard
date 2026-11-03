"""确定性 SQL 生成：注册指标 → 模板化 SELECT。

已注册指标走「度量 + 聚合 + 白名单表 + 维度过滤 + 行级权限条件」的确定性拼装，
高敏感口径由此锁定，不交给模型自由发挥。
"""

from __future__ import annotations

from typing import Optional

from ..semantic.models import Metric


def _quote(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def build_sql(
    metric: Metric,
    filters: dict[str, str],
    row_perm_condition: Optional[str],
) -> str:
    select = f"{metric.agg}({metric.measure}) AS value"
    where: list[str] = []

    for col, val in filters.items():
        if col in metric.dim_columns:
            where.append(f"{col} = {_quote(val)}")

    if row_perm_condition:
        where.append(row_perm_condition)

    sql = f"SELECT {select} FROM {metric.table}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    return sql
