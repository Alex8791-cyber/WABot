from unittest.mock import patch


def test_webhook_charge_success(client, test_db):
    """Paystack charge.success webhook updates payment status."""
    # First insert a pending payment
    from database import get_db
    conn = get_db()
    conn.execute(
        "INSERT INTO payments (reference, amount, email, status) VALUES (?, ?, ?, ?)",
        ("ref_test123", 5000000, "test@test.co.za", "pending"),
    )
    conn.commit()
    conn.close()

    resp = client.post("/payments/webhook", json={
        "event": "charge.success",
        "data": {
            "reference": "ref_test123",
            "amount": 5000000,
            "id": 99999,
            "paid_at": "2026-04-01T10:00:00Z",
        }
    })
    assert resp.status_code == 200

    # Verify DB was updated
    conn = get_db()
    row = conn.execute("SELECT status, paid_at FROM payments WHERE reference = ?", ("ref_test123",)).fetchone()
    conn.close()
    assert row["status"] == "paid"


def test_webhook_ignores_other_events(client):
    resp = client.post("/payments/webhook", json={
        "event": "transfer.success",
        "data": {},
    })
    assert resp.status_code == 200


def test_get_payment_status(client, test_db):
    from database import get_db
    conn = get_db()
    conn.execute(
        "INSERT INTO payments (reference, amount, currency, email, status, service_id) VALUES (?, ?, ?, ?, ?, ?)",
        ("ref_status1", 5000000, "ZAR", "test@test.co.za", "paid", "pentesting"),
    )
    conn.commit()
    conn.close()

    resp = client.get("/payments/status/ref_status1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"
    assert resp.json()["amount"] == 5000000


def test_get_payment_status_not_found(client, test_db):
    with patch("routes.payments.verify_transaction") as mock_verify:
        mock_verify.return_value = {"error": "not found"}
        resp = client.get("/payments/status/nonexistent")
        assert resp.status_code == 404


def test_list_payments(client, test_db):
    from database import get_db
    conn = get_db()
    conn.execute(
        "INSERT INTO payments (reference, amount, email, status, session_id) VALUES (?, ?, ?, ?, ?)",
        ("ref_list1", 1000, "a@b.com", "pending", "s1"),
    )
    conn.execute(
        "INSERT INTO payments (reference, amount, email, status, session_id) VALUES (?, ?, ?, ?, ?)",
        ("ref_list2", 2000, "c@d.com", "paid", "s2"),
    )
    conn.commit()
    conn.close()

    resp = client.get("/payments/list")
    assert resp.status_code == 200
    assert len(resp.json()["payments"]) == 2


def test_list_payments_filtered(client, test_db):
    from database import get_db
    conn = get_db()
    conn.execute(
        "INSERT INTO payments (reference, amount, email, status, session_id) VALUES (?, ?, ?, ?, ?)",
        ("ref_f1", 1000, "a@b.com", "pending", "s1"),
    )
    conn.execute(
        "INSERT INTO payments (reference, amount, email, status, session_id) VALUES (?, ?, ?, ?, ?)",
        ("ref_f2", 2000, "c@d.com", "paid", "s1"),
    )
    conn.commit()
    conn.close()

    resp = client.get("/payments/list", params={"status": "paid"})
    assert resp.status_code == 200
    assert len(resp.json()["payments"]) == 1
    assert resp.json()["payments"][0]["status"] == "paid"
