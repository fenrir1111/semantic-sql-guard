def test_parse_sqlite():
    from semantic_sql_guard import db

    kind, conf = db._parse("sqlite:///./data/business.db")
    assert kind == "sqlite"
    assert conf["path"] == "./data/business.db"


def test_parse_postgres():
    from semantic_sql_guard import db

    kind, conf = db._parse("postgresql://u:p@h:5432/biz")
    assert kind == "postgres"
    assert conf["host"] == "h"
    assert conf["dbname"] == "biz"
    assert conf["port"] == 5432


def test_parse_mysql():
    from semantic_sql_guard import db

    kind, conf = db._parse("mysql://u:p@h:3306/biz")
    assert kind == "mysql"
    assert conf["dbname"] == "biz"


def test_parse_unsupported():
    from semantic_sql_guard import db

    try:
        db._parse("oracle://x")
    except RuntimeError:
        return
    raise AssertionError("应抛出 RuntimeError")


def test_sqlite_roundtrip(tmp_path):
    from semantic_sql_guard import db

    url = f"sqlite:///{tmp_path / 't.db'}"
    db.init_db(url)
    cols, rows = db.run_select(
        "SELECT SUM(amount) AS value FROM sales WHERE region='华东' AND quarter='2026Q1'", url
    )
    assert cols == ["value"]
    assert rows[0][0] == 200000.0
