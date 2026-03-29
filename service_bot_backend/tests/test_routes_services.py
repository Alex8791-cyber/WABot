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

def test_create_lead(client, tmp_path, monkeypatch):
    monkeypatch.setattr("storage.LEADS_FILE", str(tmp_path / "leads.json"))
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
