# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/) 与语义化版本。

## [0.1.0] - 2026-11-03

### Added
- 语义注册表（指标 + 业务术语 + 敏感表 + 行级权限映射），YAML 配置驱动。
- 确定性 SQL 生成：已注册指标走「度量 + 聚合 + 白名单表 + 维度过滤 + 行级权限」模板。
- SQL 静态安全网关：仅 `SELECT`、拦截多语句与高危关键字、表白名单、敏感表按角色拦截（sqlglot 解析 + 正则兜底）。
- 行级权限：在 SQL 生成阶段注入角色可见行条件；未配置角色安全拦截。
- 结果异常校验：空结果 / 聚合 NULL / 数值超限 / 行数过多。
- 全链路审计日志：JSONL 落盘 + 内存环形缓冲，`GET /audit` 可查。
- FastAPI 接口：`POST /ask`、`GET /health`、`GET /metrics`、`GET /audit`。
- 全链路 demo（`make demo`）与 pytest 测试（29 用例全绿）。
- 工程化：`Makefile`、`Dockerfile`、`docker-compose.yml`、`.env.example`、PRD / architecture / limitation 文档、样例评测集。
- 可选 LLM 候选 SQL（litellm，默认关闭）与可选 Streamlit 可视化后台。

> 说明：当前为 v0 版本，定位 POC / 试点交付辅助底座，**不建议不经评估直接上核心生产**。

## [0.0.1] - 2026-11-03
### Planned
- v0.2：结果波动趋势校验、慢查询熔断、查询限流
- v0.3：badcase 自动回流、对接 enterprise-ai-eval-harness 评测
- v0.4：可视化语义配置后台、PostgreSQL/MySQL 数仓适配
