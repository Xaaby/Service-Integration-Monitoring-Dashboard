from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_endpoint_shape():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert body.get("status") == "ok"

