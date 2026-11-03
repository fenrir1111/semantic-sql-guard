"""可选 LLM 候选 SQL 生成（未注册指标兜底）。

默认关闭：未注册指标会被安全拦截。开启后由 LLM 生成候选 SQL，
但仍必须通过静态安全网关 + 白名单 + 敏感表校验，失败即回退拦截。
litellm 为可选依赖，未安装时自动降级。
"""

from __future__ import annotations

from typing import Optional

from .config import get_settings
from .semantic.models import Registry


def llm_enabled() -> bool:
    return bool(get_settings().llm_enabled)


def _schema_text(registry: Registry) -> str:
    lines = []
    seen = set()
    for m in registry.metrics.values():
        if m.table in seen:
            continue
        seen.add(m.table)
        lines.append(f"表 {m.table}：维度列 {', '.join(m.dim_columns)}，度量列 {m.measure}")
    return "\n".join(lines)


def generate_sql(question: str, registry: Registry) -> Optional[str]:
    """为「未注册指标」生成候选 SELECT。任何失败返回 None（走拦截）。"""
    s = get_settings()
    try:
        import litellm
    except Exception:
        return None
    try:
        prompt = (
            "你是 Text2SQL 助手。只输出一条 SELECT 语句，不要解释，不要分号结尾。\n"
            f"表结构：\n{_schema_text(registry)}\n"
            f"用户问题：{question}\nSELECT："
        )
        kwargs: dict = {"model": s.llm_model, "messages": [{"role": "user", "content": prompt}]}
        if s.llm_api_base:
            kwargs["api_base"] = s.llm_api_base
        if s.llm_api_key:
            kwargs["api_key"] = s.llm_api_key
        resp = litellm.completion(**kwargs)
        sql = (resp["choices"][0]["message"]["content"] or "").strip().strip("`").strip()
        return sql if sql.upper().startswith("SELECT") else None
    except Exception:
        return None
