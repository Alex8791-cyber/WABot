def test_get_features_config(client):
    resp = client.get("/features/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "enable_audio" in data
    assert "enable_images" in data

def test_update_features_requires_admin(client, monkeypatch):
    monkeypatch.setattr("auth.cfg.ADMIN_TOKEN", "secret")
    resp = client.post("/features/config", json={"enable_audio": True})
    assert resp.status_code == 401
