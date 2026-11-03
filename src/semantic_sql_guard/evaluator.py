"""评测 runner：读样例评测集，跑回归，输出准确率报告（效果评估闭环）。

运行：
    uv run python -m semantic_sql_guard.evaluator
    make eval

报告字段可被 enterprise-ai-eval-harness 复用（业务准确率 / 失败回流）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .config import get_settings
from .pipeline import Pipeline
from .semantic.registry import load_registry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = PROJECT_ROOT / "docs" / "eval-dataset" / "sample_eval.json"


def check_case(case: dict, result: dict) -> tuple[bool, str]:
    """把单条用例的期望与实际结果比对。"""
    problems: list[str] = []
    if case.get("expect_status") and result["status"] != case["expect_status"]:
        problems.append(f"status={result['status']}!={case['expect_status']}")
    if "expect_value" in case:
        got = result.get("result_value")
        exp = case["expect_value"]
        if not (isinstance(got, (int, float)) and abs(got - exp) < 1e-6):
            problems.append(f"value={got}!={exp}")
    if case.get("expect_result_status") and result.get("result_status") != case["expect_result_status"]:
        problems.append(f"result_status={result.get('result_status')}!={case['expect_result_status']}")
    if case.get("expect_reason_contains") and case["expect_reason_contains"] not in (result.get("answer") or ""):
        problems.append(f"answer 未包含 '{case['expect_reason_contains']}'")
    return (not problems), "; ".join(problems)


def run_eval(
    dataset_path: Path = DEFAULT_DATASET,
    registry_path: Optional[str] = None,
    database_url: Optional[str] = None,
    audit_path: Optional[str] = None,
) -> dict[str, Any]:
    s = get_settings()
    registry = load_registry(registry_path or s.registry_path)
    pipe = Pipeline(registry, database_url or s.database_url, audit_path or s.audit_log_path)

    data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    results = []
    for case in cases:
        r = pipe.run(case["question"], case.get("role", "national"))
        ok, why = check_case(case, r)
        results.append(
            {
                "id": case.get("id"),
                "question": case["question"],
                "role": case.get("role"),
                "passed": ok,
                "why": why or None,
                "status": r["status"],
                "result_status": r.get("result_status"),
                "value": r.get("result_value"),
            }
        )

    total = len(results)
    passed = sum(1 for x in results if x["passed"])
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "accuracy": (passed / total) if total else 0.0,
        "results": results,
    }


def format_report(report: dict) -> str:
    lines = [
        "=" * 60,
        "semantic-sql-guard 评测报告",
        "=" * 60,
        f"总数 {report['total']}  通过 {report['passed']}  失败 {report['failed']}  "
        f"准确率 {report['accuracy'] * 100:.1f}%",
        "-" * 60,
    ]
    for x in report["results"]:
        mark = "PASS" if x["passed"] else "FAIL"
        line = f"{str(x['id']):<4} {x['question']:<16} [{mark}]"
        if not x["passed"]:
            line += f"  -> {x['why']}"
        lines.append(line)
    lines.append("=" * 60)
    return "\n".join(lines)


def main() -> None:
    report = run_eval()
    print(format_report(report))
    out = PROJECT_ROOT / "data" / "eval_last_run.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n评测结果已写入 {out}")


if __name__ == "__main__":
    main()
