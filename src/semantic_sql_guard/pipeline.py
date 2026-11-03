"""核心链路编排：自然语言 → 语义匹配 → 敏感表/行权限 → SQL 生成 → 静态网关 → 执行 → 结果校验 → 审计。"""

from __future__ import annotations

from typing import Any, Optional

from . import db, llm
from .audit import AuditLogger
from .result_check import check_result
from .semantic import resolver
from .semantic.models import Registry
from .sql import generator, row_permission
from .sql.safety_gate import audit_sql


class Pipeline:
    def __init__(self, registry: Registry, database_url: str, audit_path: str):
        self.registry = registry
        self.database_url = database_url
        self.audit = AuditLogger(audit_path)
        db.init_db(database_url)

    def run(self, question: str, role: str) -> dict[str, Any]:
        reg = self.registry
        metric, filters = resolver.resolve(question, reg)

        base: dict[str, Any] = {
            "question": question,
            "role": role,
            "metric_id": None,
            "generated_sql": None,
            "row_permission_applied": False,
        }

        def _reject(reason: str, status: str = "rejected") -> dict:
            audit_id = self.audit.record(status=status, reason=reason, **base)
            return {
                "status": status,
                "answer": reason,
                "metric": None,
                "generated_sql": base.get("generated_sql"),
                "executed_sql": None,
                "row_permission_applied": base.get("row_permission_applied", False),
                "flags": [reason],
                "result_status": status,
                "result_value": None,
                "audit_id": audit_id,
            }

        # 1) 指标匹配
        if metric is None:
            candidate = llm.generate_sql(question, reg) if llm.llm_enabled() else None
            if candidate:
                ok, why = audit_sql(candidate, reg, role)
                base["generated_sql"] = candidate
                if not ok:
                    return _reject(f"候选 SQL 未通过安全网关：{why}")
                return self._execute(
                    candidate, reg, None, base, answer_prefix="【未注册指标·LLM候选】"
                )
            return _reject("未匹配到已注册指标，请先在语义注册表中注册该指标后再查询")

        base["metric_id"] = metric.id
        base["metric_name"] = metric.name

        # 2) 敏感表拦截
        if metric.table in reg.sensitive_tables and role not in reg.sensitive_allowed_roles:
            return _reject(
                f"敏感表访问被拦截：表 {metric.table} 仅允许角色 {sorted(reg.sensitive_allowed_roles)} 访问"
            )

        # 3) 行级权限
        rp_cond, rp_applied, rp_blocked = row_permission.apply_row_permission(
            metric, role, reg.row_permission
        )
        if rp_blocked:
            return _reject(f"角色 {role} 未配置行级权限，为安全起见已拦截")
        base["row_permission_applied"] = rp_applied

        # 4) 生成 SQL
        sql = generator.build_sql(metric, filters, rp_cond)
        base["generated_sql"] = sql

        # 5) 静态安全网关
        ok, why = audit_sql(sql, reg, role)
        if not ok:
            return _reject(f"SQL 未通过静态安全校验：{why}")

        # 6) 执行 + 结果校验 + 审计
        return self._execute(sql, reg, metric, base, answer_prefix=f"【{metric.name}】")

    def _execute(
        self,
        sql: str,
        reg: Registry,
        metric: Optional[Any],
        base: dict[str, Any],
        answer_prefix: str,
    ) -> dict[str, Any]:
        columns, rows = db.run_select(sql, self.database_url)

        if metric is None:
            flags, result_status = [], "ok"
        else:
            flags, result_status = check_result(columns, rows, metric)

        if rows and len(rows) == 1 and len(columns) == 1:
            value: Any = rows[0][0]
        elif rows:
            value = [list(r) for r in rows]
        else:
            value = None

        if result_status == "empty":
            answer = f"{answer_prefix}{flags[0] if flags else '无数据'}"
        elif result_status == "rejected":
            answer = f"{answer_prefix}{flags[0] if flags else '结果异常被拦截'}"
        else:
            answer = f"{answer_prefix}查询结果：{value}"
            if base.get("row_permission_applied"):
                answer += f"（已按角色 {base.get('role')} 的行级权限过滤）"

        audit_id = self.audit.record(
            status="answered",
            result_status=result_status,
            reason="; ".join(flags) if flags else None,
            result_value=value,
            executed_sql=sql,
            **base,
        )

        return {
            "status": "answered",
            "answer": answer,
            "metric": {"id": metric.id, "name": metric.name} if metric else None,
            "generated_sql": sql,
            "executed_sql": sql,
            "row_permission_applied": base.get("row_permission_applied", False),
            "flags": flags,
            "result_status": result_status,
            "result_value": value,
            "audit_id": audit_id,
        }
