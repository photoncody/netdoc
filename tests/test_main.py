import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "auth_required" in data
    assert "logged_in" in data

def test_security_headers():
    response = client.get("/api/status")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

def test_create_device_unauthenticated(setup_db):
    # Check if auth is enabled
    status_res = client.get("/api/status")
    auth_required = status_res.json()["auth_required"]

    device_data = {
        "name": "Test Device",
        "device_type": "Router",
        "location": "Lab"
    }

    response = client.post("/api/devices", json=device_data)

    if auth_required:
        assert response.status_code == 401
    else:
        assert response.status_code == 200
        assert response.json()["name"] == "Test Device"

        # Cleanup
        dev_id = response.json()["id"]
        client.delete(f"/api/devices/{dev_id}")

def test_read_devices(setup_db):
    response = client.get("/api/devices")
    status_res = client.get("/api/status")

    if status_res.json()["auth_required"]:
        assert response.status_code == 401
    else:
        assert response.status_code == 200
        assert isinstance(response.json(), list)

def test_create_and_delete_device(setup_db):
    # Only if auth not required
    status_res = client.get("/api/status")
    if not status_res.json()["auth_required"]:
        device_data = {
            "name": "Lifecycle Device",
            "device_type": "Switch",
            "location": "Rack 1"
        }
        create_res = client.post("/api/devices", json=device_data)
        assert create_res.status_code == 200
        dev_id = create_res.json()["id"]

        get_res = client.get("/api/devices")
        assert any(d["id"] == dev_id for d in get_res.json())

        del_res = client.delete(f"/api/devices/{dev_id}")
        assert del_res.status_code == 200

        get_res_after = client.get("/api/devices")
        assert not any(d["id"] == dev_id for d in get_res_after.json())
