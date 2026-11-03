"""语义问数控制台（可选依赖 streamlit）。

运行： uv run streamlit run src/semantic_sql_guard/streamlit_app.py

页签：查询 / 语义配置（看+改+保存注册表） / 审计日志 / 评测
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

# Streamlit 以「独立脚本」方式执行本文件（无 __package__），相对导入会直接 ImportError。
# 这里把 src/ 加入 sys.path 并改用绝对导入，保证「clone 即跑」和「已安装」两种场景都能启动。
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from semantic_sql_guard.config import get_settings  # noqa: E402
from semantic_sql_guard.evaluator import format_report, run_eval  # noqa: E402
from semantic_sql_guard.pipeline import Pipeline  # noqa: E402
from semantic_sql_guard.semantic.models import Metric  # noqa: E402
from semantic_sql_guard.semantic.registry import load_registry, save_registry  # noqa: E402

st.set_page_config(page_title="semantic-sql-guard 控制台", layout="wide")
st.title("semantic-sql-guard 语义问数控制台")
st.caption("企业语义问数安全网关：语义层 + SQL 静态安全 + 行级权限 + 结果校验 + 全链路审计")

_s = get_settings()
REG_PATH = Path(_s.registry_path)


def _load():
    return load_registry(REG_PATH)


if "registry" not in st.session_state:
    st.session_state.registry = _load()

reg = st.session_state.registry
pipe = Pipeline(reg, _s.database_url, _s.audit_log_path)

tab_q, tab_c, tab_a, tab_e = st.tabs(["查询", "语义配置", "审计日志", "评测"])

# ---------------- 查询 ----------------
with tab_q:
    st.subheader("自然语言问数")
    c1, c2 = st.columns([3, 1])
    q = c1.text_input("问题", "一季度华东区域营收")
    _rp = reg.row_permission
    _roles = list(_rp.role_values) if _rp else ["national"]
    role = c2.selectbox("角色", list(dict.fromkeys(_roles + ["hr", "west"])))
    if st.button("查询"):
        r = pipe.run(q, role)
        st.write("回答：", r["answer"])
        st.write("状态：", f"{r['status']} / {r['result_status']}")
        if r["generated_sql"]:
            st.code(r["generated_sql"])
        st.write("标记：", r["flags"])
        st.json(
            {
                "result_value": r.get("result_value"),
                "row_permission_applied": r.get("row_permission_applied"),
            }
        )

# ---------------- 语义配置 ----------------
with tab_c:
    st.subheader("已注册指标")
    st.dataframe(
        [
            {
                "id": m.id,
                "name": m.name,
                "table": m.table,
                "measure": m.measure,
                "agg": m.agg,
                "dims": m.dim_columns,
                "sensitive": m.sensitive,
                "max_value": m.max_value,
                "aliases": m.aliases,
            }
            for m in reg.metrics.values()
        ],
        use_container_width=True,
    )
    st.subheader("新增指标（先加到内存，点保存才写盘）")
    with st.form("add_metric"):
        f_id = st.text_input("指标 id", placeholder="region_profit")
        f_name = st.text_input("指标名称", placeholder="区域利润")
        f_aliases = st.text_input("别名（逗号分隔）", placeholder="利润,区域利润")
        f_table = st.text_input("表", placeholder="sales")
        f_measure = st.text_input("度量列", placeholder="profit")
        f_agg = st.selectbox("聚合", ["SUM", "COUNT", "AVG", "MAX", "MIN"])
        f_dims = st.text_input("维度列（逗号分隔）", placeholder="region,quarter")
        f_sensitive = st.checkbox("敏感指标")
        if st.form_submit_button("添加到内存") and all([f_id, f_name, f_table, f_measure]):
            reg.metrics[f_id] = Metric(
                id=f_id,
                name=f_name,
                aliases=[a.strip() for a in f_aliases.split(",") if a.strip()],
                table=f_table,
                measure=f_measure,
                agg=f_agg,
                dim_columns=[d.strip() for d in f_dims.split(",") if d.strip()],
                sensitive=f_sensitive,
            )
            st.success(f"已添加指标 {f_id}（内存生效，需「保存」持久化）")
    st.subheader("敏感表 / 白名单 / 行级权限")
    st.write("敏感表：", sorted(reg.sensitive_tables))
    st.write("白名单角色：", sorted(reg.sensitive_allowed_roles))
    if reg.row_permission:
        st.write("行级权限列：", reg.row_permission.column)
        st.write(reg.row_permission.role_values)
    col1, col2 = st.columns(2)
    if col1.button("保存到 registry.yaml"):
        save_registry(reg, REG_PATH)
        st.success("已保存到 registry.yaml")
    if col2.button("重新加载 registry.yaml"):
        st.session_state.registry = _load()
        st.rerun()

# ---------------- 审计日志 ----------------
with tab_a:
    st.subheader("全链路审计（读取 audit.log）")
    _apath = Path(_s.audit_log_path)
    if _apath.exists():
        recs = [json.loads(l) for l in _apath.read_text(encoding="utf-8").splitlines() if l.strip()][-50:]
        st.dataframe(list(reversed(recs)), use_container_width=True)
    else:
        st.write("暂无审计记录")

# ---------------- 评测 ----------------
with tab_e:
    st.subheader("跑样例评测集")
    if st.button("运行评测"):
        report = run_eval(
            registry_path=str(REG_PATH),
            database_url=_s.database_url,
            audit_path=_s.audit_log_path,
        )
        st.success(f"准确率 {report['accuracy'] * 100:.1f}%（{report['passed']}/{report['total']}）")
        st.code(format_report(report))
