from semantic_sql_guard.result_check import check_result


def test_empty_result(registry):
    flags, status = check_result(["value"], [], registry.metrics["region_revenue"])
    assert status == "empty" and flags


def test_null_aggregate(registry):
    flags, status = check_result(["value"], [(None,)], registry.metrics["region_revenue"])
    assert status == "empty" and any("NULL" in f for f in flags)


def test_value_over_threshold_rejected(registry):
    flags, status = check_result(
        ["value"], [(99999999999,)], registry.metrics["region_revenue"]
    )
    assert status == "rejected" and any("超限" in f for f in flags)


def test_normal_value_ok(registry):
    flags, status = check_result(["value"], [(200000.0,)], registry.metrics["region_revenue"])
    assert status == "ok" and flags == []
