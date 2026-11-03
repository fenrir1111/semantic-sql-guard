def test_match_metric_and_terms(registry):
    from semantic_sql_guard.semantic import resolver

    m, f = resolver.resolve("一季度华东区域营收", registry)
    assert m is not None and m.id == "region_revenue"
    assert f == {"region": "华东", "quarter": "2026Q1"}


def test_longest_alias_wins(registry):
    from semantic_sql_guard.semantic import resolver

    m, _ = resolver.resolve("华东区域营收", registry)
    assert m.id == "region_revenue"


def test_term_outside_dim_ignored(registry):
    from semantic_sql_guard.semantic import resolver

    # 研发部(dept) 不属于 region_revenue 的维度列，应被忽略
    m, f = resolver.resolve("研发部一季度区域营收", registry)
    assert m.id == "region_revenue"
    assert f.get("quarter") == "2026Q1"
    assert "dept" not in f


def test_no_match(registry):
    from semantic_sql_guard.semantic import resolver

    m, f = resolver.resolve("今天天气如何", registry)
    assert m is None and f == {}
