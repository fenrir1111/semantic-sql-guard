from fastapi.testclient import TestClient

from semantic_sql_guard.main import build_app


def _client(pipeline):
    return TestClient(build_app(pipeline))


def test_health(pipeline):
    with _client(pipeline) as c:
        r = c.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_ask_end_to_end(pipeline):
    with _client(pipeline) as c:
        r = c.post("/ask", json={"question": "一季度华东区域营收", "role": "east"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "answered"
        assert data["result_value"] == 200000.0


def test_metrics_list(pipeline):
    with _client(pipeline) as c:
        r = c.get("/metrics")
        assert r.status_code == 200
        assert {"region_revenue", "employee_salary_total"} <= {m["id"] for m in r.json()}


def test_audit_logs(pipeline):
    with _client(pipeline) as c:
        c.post("/ask", json={"question": "一季度区域营收", "role": "national"})
        r = c.get("/audit")
        assert r.status_code == 200
        assert len(r.json()) >= 1
