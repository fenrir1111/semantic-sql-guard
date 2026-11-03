def test_registered_metric_with_row_permission(pipeline):
    r = pipeline.run("一季度华东区域营收", "east")
    assert r["status"] == "answered"
    assert r["result_status"] == "ok"
    assert r["result_value"] == 200000.0
    assert r["row_permission_applied"] is True
    assert "region IN" in r["generated_sql"]


def test_row_permission_out_of_scope_empty(pipeline):
    r = pipeline.run("一季度华南区域营收", "east")
    assert r["status"] == "answered"
    assert r["result_status"] == "empty"


def test_national_full_range(pipeline):
    r = pipeline.run("一季度区域营收", "national")
    assert r["result_status"] == "ok"
    assert r["result_value"] == 505000.0


def test_count_metric(pipeline):
    r = pipeline.run("一季度订单量", "south")
    assert r["result_status"] == "ok"
    assert r["result_value"] == 2


def test_unknown_role_blocked(pipeline):
    r = pipeline.run("一季度区域营收", "west")
    assert r["status"] == "rejected"
    assert "行级权限" in r["answer"]


def test_sensitive_table_blocked(pipeline):
    r = pipeline.run("员工薪酬总额", "east")
    assert r["status"] == "rejected"
    assert "敏感表" in r["answer"]


def test_sensitive_table_allowed(pipeline):
    r = pipeline.run("员工薪酬总额", "national")
    assert r["status"] == "answered"
    assert r["result_value"] == 115000.0


def test_unregistered_metric_rejected(pipeline):
    r = pipeline.run("今天天气怎么样", "national")
    assert r["status"] == "rejected"
    assert "未匹配" in r["answer"]


def test_audit_records_written(pipeline):
    pipeline.run("一季度华东区域营收", "east")
    pipeline.run("今天天气怎么样", "national")
    recs = pipeline.audit.recent(10)
    assert len(recs) == 2
    assert recs[0]["status"] == "answered"
    assert recs[1]["status"] == "rejected"
