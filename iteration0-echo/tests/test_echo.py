from fastapi.testclient import TestClient

from server import app

client = TestClient(app)


def test_echo_returns_same_message():
    resp = client.post("/echo", json={"message": "hello"})
    assert resp.status_code == 200
    assert resp.json() == {"echo": "hello"}


def test_echo_rejects_missing_message():
    resp = client.post("/echo", json={})
    assert resp.status_code == 422


def test_health():
    assert client.get("/health").json() == {"status": "ok"}
