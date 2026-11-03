"""业务数据访问层。

支持三种后端（由 DATABASE_URL 决定）：
- `sqlite:///...`     内嵌 SQLite（POC 零配置，默认，自动播种样例数据）
- `postgresql://u:p@h:port/db`  PostgreSQL（可选依赖 psycopg）
- `mysql://u:p@h:port/db`       MySQL（可选依赖 PyMySQL）

生产环境把 DATABASE_URL 指向 PostgreSQL/MySQL 数仓即可。
安全：查询走只读连接 / 只读事务，从驱动层杜绝写操作。
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any
from urllib.parse import urlparse

# ---- 样例业务数据（首次播种） ----
_SAMPLE_SALES = [
    ("S001", "华东", "2026Q1", 120000.0),
    ("S002", "华东", "2026Q1", 80000.0),
    ("S003", "华北", "2026Q1", 150000.0),
    ("S004", "华南", "2026Q1", 95000.0),
    ("S005", "华中", "2026Q1", 60000.0),
    ("S006", "华东", "2026Q2", 130000.0),
    ("S007", "华北", "2026Q2", 140000.0),
    ("S008", "华南", "2026Q2", 110000.0),
    ("S009", "华中", "2026Q2", 70000.0),
    ("S010", "华东", "2026Q3", 160000.0),
]
_SAMPLE_SALARY = [
    ("E001", "研发", 30000.0),
    ("E002", "研发", 32000.0),
    ("E003", "销售", 25000.0),
    ("E004", "销售", 28000.0),
]
_SAMPLE_BANK = [
    ("6222-0001", "张三", 500000.0),
    ("6222-0002", "李四", 320000.0),
]

_DDL = [
    "CREATE TABLE IF NOT EXISTS sales (order_id TEXT, region TEXT, quarter TEXT, amount REAL)",
    "CREATE TABLE IF NOT EXISTS hr_salary (emp_id TEXT, dept TEXT, monthly_salary REAL)",
    "CREATE TABLE IF NOT EXISTS bank_account (account_no TEXT, holder TEXT, balance REAL)",
]

_SEED = [
    ("sales", 4, _SAMPLE_SALES),
    ("hr_salary", 3, _SAMPLE_SALARY),
    ("bank_account", 3, _SAMPLE_BANK),
]


def _parse(url: str) -> tuple[str, dict]:
    if url.startswith("sqlite"):
        path = url.split("///", 1)[-1] if "///" in url else url
        return "sqlite", {"path": path}
    p = urlparse(url)
    if p.scheme in ("postgresql", "postgres"):
        return "postgres", {
            "host": p.hostname,
            "port": p.port or 5432,
            "user": p.username,
            "password": p.password,
            "dbname": (p.path or "").lstrip("/"),
        }
    if p.scheme in ("mysql", "mysql+pymysql"):
        return "mysql", {
            "host": p.hostname,
            "port": p.port or 3306,
            "user": p.username,
            "password": p.password,
            "dbname": (p.path or "").lstrip("/"),
        }
    raise RuntimeError(
        f"不支持的数据库连接串：{url}（支持 sqlite:///、postgresql://、mysql://）"
    )


def init_db(url: str) -> None:
    """建表（若不存在）并在为空时播种样例数据。幂等。"""
    kind, conf = _parse(url)
    if kind == "sqlite":
        _init_sqlite(conf["path"])
    elif kind == "postgres":
        _init_postgres(conf)
    elif kind == "mysql":
        _init_mysql(conf)


def run_select(sql: str, url: str) -> tuple[list[str], list[tuple[Any, ...]]]:
    """以只读方式执行 SELECT，返回 (列名, 行元组列表)。"""
    kind, conf = _parse(url)
    if kind == "sqlite":
        return _select_sqlite(sql, conf["path"])
    if kind == "postgres":
        return _select_postgres(sql, conf)
    if kind == "mysql":
        return _select_mysql(sql, conf)
    raise RuntimeError(f"不支持的数据库后端：{kind}")


# ==================== SQLite ====================
def _cnt_sqlite(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
    return int(row["c"])


def _init_sqlite(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        for stmt in _DDL:
            conn.execute(stmt)
        for table, n, rows in _SEED:
            if _cnt_sqlite(conn, table) == 0:
                conn.executemany(f"INSERT INTO {table} VALUES ({','.join('?' * n)})", rows)
        conn.commit()
    finally:
        conn.close()


def _select_sqlite(sql: str, path: str) -> tuple[list[str], list[tuple[Any, ...]]]:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA query_only = ON")
        cur = conn.execute(sql)
        columns = [d[0] for d in cur.description]
        rows = [tuple(r) for r in cur.fetchall()]
        return columns, rows
    finally:
        conn.close()


# ==================== PostgreSQL ====================
def _pg_connect(conf: dict):
    try:
        import psycopg
    except Exception as e:  # pragma: no cover
        raise RuntimeError("PostgreSQL 需要安装 `uv pip install psycopg[binary]`") from e
    return psycopg.connect(
        host=conf["host"], port=conf["port"],
        user=conf["user"], password=conf["password"], dbname=conf["dbname"],
    )


def _cnt(cur, table: str) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0]


def _init_postgres(conf: dict) -> None:
    conn = _pg_connect(conf)
    try:
        cur = conn.cursor()
        for stmt in _DDL:
            cur.execute(stmt)
        for table, n, rows in _SEED:
            if _cnt(cur, table) == 0:
                cur.executemany(f"INSERT INTO {table} VALUES ({','.join('%s' * n)})", rows)
        conn.commit()
    finally:
        conn.close()


def _select_postgres(sql: str, conf: dict) -> tuple[list[str], list[tuple[Any, ...]]]:
    conn = _pg_connect(conf)
    try:
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute("SET TRANSACTION READ ONLY")
        cur.execute(sql)
        columns = [d[0] for d in cur.description]
        rows = [tuple(r) for r in cur.fetchall()]
        conn.commit()
        return columns, rows
    finally:
        conn.close()


# ==================== MySQL ====================
def _mysql_connect(conf: dict):
    try:
        import pymysql
    except Exception as e:  # pragma: no cover
        raise RuntimeError("MySQL 需要安装 `uv pip install PyMySQL`") from e
    return pymysql.connect(
        host=conf["host"], port=conf["port"],
        user=conf["user"], password=conf["password"], database=conf["dbname"],
    )


def _init_mysql(conf: dict) -> None:
    conn = _mysql_connect(conf)
    try:
        cur = conn.cursor()
        for stmt in _DDL:
            cur.execute(stmt)
        for table, n, rows in _SEED:
            if _cnt(cur, table) == 0:
                cur.executemany(f"INSERT INTO {table} VALUES ({','.join('%s' * n)})", rows)
        conn.commit()
    finally:
        conn.close()


def _select_mysql(sql: str, conf: dict) -> tuple[list[str], list[tuple[Any, ...]]]:
    conn = _mysql_connect(conf)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        columns = [d[0] for d in cur.description]
        rows = [tuple(r) for r in cur.fetchall()]
        return columns, rows
    finally:
        conn.close()
