"""SQL 静态安全网关：执行前对最终 SQL 做只读/白名单/敏感表校验。

叠加在数据库原生权限之上，作为上层业务风控层（不替代数据库权限）。
优先使用 sqlglot 解析，解析失败时回退到正则抽取表名，保证可用。
"""

from __future__ import annotations

import re

from ..semantic.models import Registry

_BLACKLIST = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "MERGE",
    "REPLACE",
]


def _tables_fallback(stmt: str) -> set[str]:
    tables = set()
    for m in re.findall(r"\b(?:FROM|JOIN)\s+([A-Za-z_][\w]*)", stmt, re.I):
        tables.add(m.lower())
    return tables


def audit_sql(sql: str, registry: Registry, role: str) -> tuple[bool, str]:
    """静态安全校验。返回 (是否通过, 拦截原因)。"""
    stmt = (sql or "").strip()
    if not stmt:
        return False, "SQL 为空"

    # 1) 多语句拦截
    parts = [p for p in stmt.split(";") if p.strip()]
    if len(parts) != 1:
        return False, "禁止多语句执行"

    up = stmt.upper()
    # 2) 高危关键字拦截（DML/DDL 等）
    for kw in _BLACKLIST:
        if re.search(rf"\b{kw}\b", up):
            return False, f"高危关键字被拦截：{kw}"

    # 3) 仅允许 SELECT
    if not up.startswith("SELECT"):
        return False, "仅允许 SELECT 查询"

    # 4) 解析并校验表（白名单 + 敏感表）
    try:
        import sqlglot
        from sqlglot import exp

        parsed = sqlglot.parse_one(stmt, read="postgres")
        if not isinstance(parsed, exp.Select):
            return False, "仅允许 SELECT 语句"
        tables = {t.name.lower() for t in parsed.find_all(exp.Table)}
    except Exception:
        tables = _tables_fallback(stmt)

    for t in tables:
        if t in registry.sensitive_tables and role not in registry.sensitive_allowed_roles:
            return False, f"敏感表访问被拦截：{t}"
        if t not in registry.allowed_tables:
            return False, f"表 {t} 不在指标白名单内"

    return True, ""
