from semantic_sql_guard.sql.safety_gate import audit_sql


def test_valid_select_passes(registry):
    ok, why = audit_sql(
        "SELECT SUM(amount) AS value FROM sales WHERE region='华东'", registry, "east"
    )
    assert ok, why


def test_block_drop(registry):
    ok, why = audit_sql("DROP TABLE sales", registry, "national")
    assert not ok and "DROP" in why


def test_block_multi_statement(registry):
    ok, why = audit_sql("SELECT 1; DELETE FROM sales", registry, "national")
    assert not ok and "多语句" in why


def test_block_update(registry):
    ok, why = audit_sql("UPDATE sales SET amount=0", registry, "national")
    assert not ok and "UPDATE" in why


def test_block_non_select_prefix(registry):
    ok, why = audit_sql("WITH t AS (SELECT 1) SELECT * FROM sales", registry, "national")
    assert not ok and "仅允许 SELECT" in why


def test_block_sensitive_table(registry):
    ok, why = audit_sql(
        "SELECT SUM(monthly_salary) AS value FROM hr_salary", registry, "east"
    )
    assert not ok and "敏感表" in why


def test_allow_sensitive_for_whitelist_role(registry):
    ok, why = audit_sql(
        "SELECT SUM(monthly_salary) AS value FROM hr_salary", registry, "national"
    )
    assert ok, why


def test_block_unknown_table(registry):
    ok, why = audit_sql("SELECT * FROM secret_tbl", registry, "national")
    assert not ok and "白名单" in why
