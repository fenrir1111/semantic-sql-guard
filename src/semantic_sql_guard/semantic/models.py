"""语义层数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Metric:
    """注册指标：把业务口径映射到「表 + 度量 + 聚合 + 维度列」。"""

    id: str
    name: str
    aliases: list[str]
    table: str
    measure: str
    agg: str  # SUM / COUNT / AVG / MAX / MIN
    dim_columns: list[str]
    sensitive: bool = False
    max_value: Optional[float] = None  # 结果异常校验阈值
    description: str = ""


@dataclass
class Term:
    """业务术语：自然语言词 → 列 / 值。"""

    word: str
    column: str
    value: str


@dataclass
class RowPermission:
    """行级权限：role → 允许访问的某列取值。"""

    column: str
    role_values: dict[str, list[str]]


@dataclass
class Registry:
    """语义注册表。"""

    metrics: dict[str, Metric] = field(default_factory=dict)
    terms: list[Term] = field(default_factory=list)
    sensitive_tables: set[str] = field(default_factory=set)
    sensitive_allowed_roles: set[str] = field(default_factory=set)
    row_permission: Optional[RowPermission] = None

    @property
    def allowed_tables(self) -> set[str]:
        """白名单：所有已注册指标引用的表。"""
        return {m.table for m in self.metrics.values()}
