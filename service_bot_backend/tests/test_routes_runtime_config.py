def test_get_runtime_config(admin_client):
    resp = admin_client.get("/runtime/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "MODEL_NAME" in data
    assert "RATE_LIMIT_REQUESTS" in data
    assert "HANDOFF_THRESHOLD" in data


def test_get_runtime_config_masks_secrets(admin_client, monkeypatch):
    monkeypatch.setattr("config.PAYSTACK_SECRET_KEY", "sk_live_realkey")
    resp = admin_client.get("/runtime/config")
    data = resp.json()
    assert data["PAYSTACK_SECRET_KEY"] == "***"


def test_get_runtime_config_requires_admin(client, monkeypatch):
    monkeypatch.setattr("auth.cfg.ADMIN_TOKEN", "secret")
    resp = client.get("/runtime/config")
    assert resp.status_code == 401


def test_update_runtime_config(admin_client, test_db):
    resp = admin_client.post("/runtime/config", json={
        "MODEL_NAME": "gpt-4o",
        "RATE_LIMIT_REQUESTS": "50",
    })
    assert resp.status_code == 200
    assert "MODEL_NAME" in resp.json()["changed"]
    assert "RATE_LIMIT_REQUESTS" in resp.json()["changed"]

    # Verify the values were applied
    import config
    assert config.MODEL_NAME == "gpt-4o"
    assert config.RATE_LIMIT_REQUESTS == 50

    # Verify persisted to DB
    from database import get_db
    conn = get_db()
    row = conn.execute("SELECT value FROM runtime_config WHERE key = ?", ("MODEL_NAME",)).fetchone()
    conn.close()
    assert row["value"] == "gpt-4o"


def test_update_runtime_config_ignores_invalid_keys(admin_client, test_db):
    resp = admin_client.post("/runtime/config", json={
        "INVALID_KEY": "value",
        "MODEL_NAME": "gpt-3.5-turbo",
    })
    assert resp.status_code == 200
    assert "MODEL_NAME" in resp.json()["changed"]
    assert "INVALID_KEY" not in resp.json()["changed"]


def test_update_runtime_config_rejects_non_mutable(admin_client, test_db):
    resp = admin_client.post("/runtime/config", json={
        "DATABASE_FILE": "/evil/path",
    })
    assert resp.status_code == 200
    assert resp.json()["changed"] == []
