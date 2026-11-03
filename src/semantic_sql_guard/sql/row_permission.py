"""行级权限：在检索/SQL 阶段按角色注入行过滤条件。

「先控权限、再做查询」——在召回阶段就收敛可见行，而不是回答后再过滤。
"""

from __future__ import annotations

from typing import Optional

from ..semantic.models import Metric, RowPermission


def apply_row_permission(
    metric: Metric, role: str, row_permission: Optional[RowPermission]
) -> tuple[Optional[str], bool, bool]:
    """返回 (SQL 条件, 是否应用, 是否拦截)。"""
    if row_permission is None:
        return None, False, False

    # 该表没有行级隔离列 → 不需要行过滤
    if row_permission.column not in metric.dim_columns:
        return None, False, False

    # 角色未配置行级权限 → 安全默认拦截
    if role not in row_permission.role_values:
        return None, False, True

    vals = row_permission.role_values[role]
    quoted = ", ".join("'" + str(v).replace("'", "''") + "'" for v in vals)
    return f"{row_permission.column} IN ({quoted})", True, False
