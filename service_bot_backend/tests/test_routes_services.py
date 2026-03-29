import pytest
import json


def test_get_services_returns_list(client):
    resp = client.get("/services")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]

def test_get_service_by_id(client):
    resp = client.get("/services/executive_it_support")
    assert resp.status_code == 200
    assert resp.json()["id"] == "executive_it_support"

def test_get_service_not_found(client):
    resp = client.get("/services/nonexistent")
    assert resp.status_code == 404

def test_create_lead(client):
    resp = client.post("/lead", json={
        "service_id": "executive_it_support",
        "responses": {"company_name": "Test GmbH"}
    })
    assert resp.status_code == 201

def test_create_lead_invalid_service(client):
    resp = client.post("/lead", json={
        "service_id": "nonexistent",
        "responses": {}
    })
    assert resp.status_code == 400


@pytest.fixture
def tmp_services(tmp_path, monkeypatch):
    """Redirect storage.SERVICES_FILE to a temp file so real services.json is untouched."""
    tmp_file = tmp_path / "services.json"
    tmp_file.write_text("[]", encoding="utf-8")
    import storage
    monkeypatch.setattr(storage, "SERVICES_FILE", str(tmp_file))
    return str(tmp_file)


def test_update_services_catalog(admin_client, tmp_services):
    new_catalog = [
        {"id": "test_svc", "name": "Test Service", "description": "A test", "delivery_mode": "Remote", "average_duration": "1 Week", "average_value": "R10k", "proposal_required": False, "questions": []}
    ]
    resp = admin_client.post("/services", json=new_catalog)
    assert resp.status_code == 200
    assert resp.json()["count"] == 1
    # Verify it was saved
    resp2 = admin_client.get("/services")
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["id"] == "test_svc"


def test_update_single_service(admin_client, tmp_services):
    # First set up a catalog
    catalog = [
        {"id": "svc1", "name": "Service One", "description": "First", "delivery_mode": "Remote", "average_duration": "1W", "average_value": "R1k", "proposal_required": False, "questions": []},
        {"id": "svc2", "name": "Service Two", "description": "Second", "delivery_mode": "Remote", "average_duration": "2W", "average_value": "R2k", "proposal_required": False, "questions": []},
    ]
    admin_client.post("/services", json=catalog)

    # Update svc1
    resp = admin_client.put("/services/svc1", json={
        "name": "Updated Service", "description": "Updated", "delivery_mode": "Hybrid",
        "average_duration": "3W", "average_value": "R5k", "proposal_required": True, "questions": []
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Service"
    assert resp.json()["id"] == "svc1"  # ID preserved


def test_delete_service(admin_client, tmp_services):
    catalog = [
        {"id": "del1", "name": "To Delete", "description": "X", "delivery_mode": "Remote", "average_duration": "1W", "average_value": "R1k", "proposal_required": False, "questions": []},
        {"id": "keep1", "name": "To Keep", "description": "Y", "delivery_mode": "Remote", "average_duration": "1W", "average_value": "R1k", "proposal_required": False, "questions": []},
    ]
    admin_client.post("/services", json=catalog)

    resp = admin_client.delete("/services/del1")
    assert resp.status_code == 200

    # Verify only keep1 remains
    resp2 = admin_client.get("/services")
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["id"] == "keep1"


def test_delete_service_not_found(admin_client, tmp_services):
    resp = admin_client.delete("/services/nonexistent_xyz")
    assert resp.status_code == 404


def test_update_services_requires_admin(client, monkeypatch):
    monkeypatch.setattr("auth.cfg.ADMIN_TOKEN", "secret")
    resp = client.post("/services", json=[])
    assert resp.status_code == 401
