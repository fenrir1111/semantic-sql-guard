"""FastAPI 服务入口。

接口：
- POST /ask      自然语言问数（带角色，用于行级权限 + 敏感表校验）
- GET  /health   健康检查
- GET  /metrics  已注册指标列表
- GET  /audit    审计日志
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

from . import db
from .config import get_settings
from .pipeline import Pipeline
from .semantic.registry import load_registry


class AskRequest(BaseModel):
    question: str = Field(..., description="自然语言问题", examples=["一季度华东区域营收"])
    role: str = Field("national", description="调用角色，用于行级权限与敏感表校验")


def build_pipeline() -> Pipeline:
    s = get_settings()
    registry = load_registry(s.registry_path)
    return Pipeline(registry, s.database_url, s.audit_log_path)


@lru_cache
def _default_pipeline() -> Pipeline:
    return build_pipeline()


def build_app(pipeline: Optional[Pipeline] = None) -> FastAPI:
    pipe = pipeline or _default_pipeline()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        db.init_db(pipe.database_url)  # 确保样例库就绪
        yield

    app = FastAPI(
        title="semantic-sql-guard",
        description=(
            "企业语义问数安全网关｜Text2SQL 语义层 + SQL 静态安全校验 "
            "+ 行级权限拦截 + 结果异常校验"
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.post("/ask")
    def ask(req: AskRequest) -> dict:
        return pipe.run(req.question, req.role)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "metrics": len(pipe.registry.metrics)}

    @app.get("/metrics")
    def metrics() -> list[dict]:
        return [
            {
                "id": m.id,
                "name": m.name,
                "table": m.table,
                "sensitive": m.sensitive,
                "aliases": m.aliases,
            }
            for m in pipe.registry.metrics.values()
        ]

    @app.get("/audit")
    def audit(limit: int = Query(50, ge=1, le=500)) -> list[dict]:
        return pipe.audit.recent(limit)

    return app


app = build_app()
