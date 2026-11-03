"""结果异常校验：即使 SQL 合法，脏/异常结果也会被标记或拦截。"""

from __future__ import annotations

from typing import Any

from .semantic.models import Metric


def check_result(
    columns: list[str], rows: list[tuple[Any, ...]], metric: Metric
) -> tuple[list[str], str]:
    """返回 (标记列表, 结果状态 ok/empty/warn/rejected)。"""
    flags: list[str] = []

    if not rows:
        flags.append("空结果：未查询到数据（可能超出角色权限范围或口径不匹配）")
        return flags, "empty"

    # 单值聚合结果
    if len(rows) == 1 and len(columns) == 1:
        value = rows[0][0]
        if value is None:
            flags.append("聚合结果为 NULL")
            return flags, "empty"
        if (
            metric.max_value is not None
            and isinstance(value, (int, float))
            and value > metric.max_value
        ):
            flags.append(f"数值超限：{value} > 阈值 {metric.max_value}")
            return flags, "rejected"

    if len(rows) > 1000:
        flags.append(f"结果行数过多：{len(rows)}")
        return flags, "warn"

    return flags, "ok"
