"""自然语言 → 指标 + 维度过滤 的解析器。

设计取向：确定性、可解释、可测试。
- 指标匹配采用「名称/别名最长命中」，命中即认为用户问的是该注册指标；
- 维度值从业务术语词典中提取，且仅接受该指标声明过的维度列；
- 未命中任何注册指标 → 返回 None（由上层决定拦截或走 LLM 候选）。
"""

from __future__ import annotations

from typing import Optional

from .models import Metric, Registry


def resolve(question: str, registry: Registry) -> tuple[Optional[Metric], dict[str, str]]:
    """返回 (匹配到的指标 | None, {列: 值} 维度过滤)。"""
    q = (question or "").strip()
    if not q:
        return None, {}

    best: Optional[Metric] = None
    best_len = 0
    for m in registry.metrics.values():
        for cand in [m.name, *m.aliases]:
            if cand and cand in q and len(cand) > best_len:
                best = m
                best_len = len(cand)

    if best is None:
        return None, {}

    filters: dict[str, str] = {}
    for t in registry.terms:
        if t.word in q and t.column in best.dim_columns and t.column not in filters:
            filters[t.column] = t.value

    return best, filters
