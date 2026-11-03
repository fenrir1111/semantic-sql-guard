"""全链路 demo：直接跑核心链路，无需起服务。

运行： uv run python -m semantic_sql_guard.demo
覆盖：注册指标命中、行级权限、越权空结果、敏感表拦截、放行、未注册拦截。
"""

from __future__ import annotations

from .config import get_settings
from .pipeline import Pipeline
from .semantic.registry import load_registry

CASES = [
    ("一季度华东区域营收", "east", "注册指标命中 + 行级权限（east→华东/华北）"),
    ("一季度华南区域营收", "east", "行级权限外：华南不在 east 范围 → 空结果"),
    ("一季度区域营收", "national", "全国角色：全区域 2026Q1"),
    ("一季度订单量", "south", "COUNT 指标 + 行级权限（south→华南/华中）"),
    ("员工薪酬总额", "east", "敏感表 hr_salary：east 非白名单 → 拦截"),
    ("研发部薪酬总额", "national", "敏感表：national 白名单 → 放行"),
    ("今天天气怎么样", "national", "未注册指标 → 拦截"),
]


def main() -> None:
    s = get_settings()
    registry = load_registry(s.registry_path)
    pipe = Pipeline(registry, s.database_url, s.audit_log_path)

    print("=" * 72)
    print("semantic-sql-guard 全链路 demo")
    print("=" * 72)
    for question, role, note in CASES:
        r = pipe.run(question, role)
        print("-" * 72)
        print(f"Q   : {question}")
        print(f"角色 : {role}   说明 : {note}")
        print(f"状态 : {r['status']} / 结果: {r['result_status']}")
        if r["generated_sql"]:
            print(f"SQL  : {r['generated_sql']}")
        print(f"回答 : {r['answer']}")
        if r["flags"] and r["flags"] != [r["answer"]]:
            print(f"标记 : {'; '.join(r['flags'])}")
    print("-" * 72)
    print(f"共 {len(CASES)} 条样例，审计记录 {len(pipe.audit.recent(500))} 条 → {s.audit_log_path}")


if __name__ == "__main__":
    main()
