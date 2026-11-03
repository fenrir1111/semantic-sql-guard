import pathlib


def test_eval_all_cases_pass(tmp_path):
    from semantic_sql_guard import evaluator

    reg = pathlib.Path(__file__).resolve().parent.parent / "data" / "registry.yaml"
    report = evaluator.run_eval(
        registry_path=str(reg),
        database_url=f"sqlite:///{tmp_path / 'e.db'}",
        audit_path=str(tmp_path / "a.log"),
    )
    assert report["total"] == 7
    assert report["passed"] == report["total"], report["results"]
    assert report["accuracy"] == 1.0


def test_eval_detects_failure(tmp_path):
    from semantic_sql_guard import evaluator

    # 构造一个故意错误期望的用例，应被判为失败
    case = {"id": "X", "question": "今天天气怎么样", "role": "national", "expect_status": "answered"}
    result = {"status": "rejected", "answer": "未匹配到已注册指标", "result_status": "rejected", "result_value": None}
    ok, why = evaluator.check_case(case, result)
    assert not ok and "status" in why
