# 贡献指南 · semantic-sql-guard

感谢你愿意参与这个项目。这个仓库的目标很明确：**把「企业问数」从「模型能写 SQL」变成「能安全上线」**。
所以任何改动，都要先回答一个问题：**这个改动会不会削弱安全边界或审计能力？**

## 快速开始

```bash
git clone https://github.com/fenrir1111/semantic-sql-guard.git
cd semantic-sql-guard

uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python -e .

.venv/bin/python -m semantic_sql_guard.demo    # 全链路 demo
.venv/bin/python -m pytest -q                   # 跑测试
.venv/bin/python -m uvicorn semantic_sql_guard.main:app --port 8000
```

没装 uv 也可以用标准 venv + pip，依赖清单在 `requirements.txt`。

## 提交前必做

```bash
.venv/bin/python -m pytest -q --basetemp="$PWD/.pytest-tmp"   # 必须全绿
.venv/bin/python -m semantic_sql_guard.demo                    # 必须退出码 0
```

CI 会自动跑上面两步，再加 FastAPI `/health` 与 Streamlit 控制台冒烟（Python 3.10 / 3.12 双版本）。

## 哪些改动受欢迎

| 类型 | 例子 |
|---|---|
| 新增行业指标样例 | 电力、烟草、港口等场景的指标注册表与术语词典 |
| 数仓适配 | 新增数据库方言的 `_select_*` 实现 |
| 安全规则 | 新的高危关键字、表白名单校验、结果异常阈值 |
| 领域扩展 | 新的指标类型、新的行级权限模型 |

## 哪些改动不会被接受

- **削弱安全边界的**：放宽 SQL 关键字黑名单、跳过敏感表校验、把行级权限改成「查询后过滤」
- **让未注册指标可以自由生成 SQL 的**（那等于把幻觉放回系统）
- **引入重量级必需依赖**：核心依赖必须保持轻量，可选能力走 `pyproject.toml` 的 extras
- **在核心链路里引入 LLM 强依赖**：默认路径必须是确定性、可复现的

## 代码约定

- **Python ≥3.10**，`from __future__ import annotations` 开头，类型标注齐全
- **行宽 100 以内**，命名 `snake_case`，公开 API 用 docstring 说明「为什么」而不是「做了什么」
- **相对导入用绝对导入**：`streamlit_app.py` 会被 Streamlit 当独立脚本执行，
  相对导入会直接 `ImportError` —— 统一写成 `from semantic_sql_guard.xxx import ...`。
  **包括 `if` 分支 / 函数里的延迟导入** —— 那类 bug 首屏正常，只有用户点到该分支才炸，
  AppTest 初始渲染和 HTTP 200 都看不出来。`tests/test_streamlit_app.py` 用 AST 全量扫描 +
  点击主按钮的交互冒烟，在 CI 里守住这条。
- **每个新功能配测试**：安全相关的改动请附上「攻击用例」——证明旧实现会放行、新实现会拦住
- **审计留痕不可省**：任何处理用户输入的路径都要落审计记录

## 提交信息

用中文或英文都可以，格式参考：

```
feat: 新增电力行业指标样例（负荷、电价）
fix: 修复多语句检测绕过（注释内分号）
docs: 补充行级权限配置说明
```

## Issue

提 Issue 时请尽量带上：

1. 复现步骤或最小样例
2. 期望行为 vs 实际行为
3. 运行环境（Python 版本、数据库类型）
4. 相关审计日志片段（**注意脱敏**，不要贴真实业务数据）

## 致谢

有效贡献会在 README 的致谢栏署名。

## License

贡献即视为同意以 MIT 协议授权你的改动。
