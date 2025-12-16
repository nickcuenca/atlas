from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_echo_validation():
    r = client.post("/jobs", json={"type":"echo","payload":{"message":"hi"}})
    assert r.status_code == 200
    data = r.json()
    assert data["state"] == "PENDING"
    assert data["type"] == "echo"

def test_invalid_type():
    r = client.post("/jobs", json={"type":"nope","payload":{}})
    assert r.status_code == 400