from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，支持 .env / 环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 业务数据库（默认 SQLite，POC 零配置；生产指向 PG/MySQL 数仓）
    database_url: str = "sqlite:///./data/business.db"
    # 语义注册表 / 审计日志路径
    registry_path: str = "./data/registry.yaml"
    audit_log_path: str = "./data/audit.log"

    # 可选 LLM（未注册指标候选 SQL）
    llm_enabled: bool = False
    llm_model: str = "gpt-4o-mini"
    llm_api_base: str = ""
    llm_api_key: str = ""

    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
