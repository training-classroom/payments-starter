from fastapi.testclient import TestClient

from tests.support import payment_body


def test_completed_and_rejected_payments_are_audited(client: TestClient) -> None:
    ok = client.post(
        "/payments",
        json=payment_body(),
        headers={"Idempotency-Key": "a-1", "X-Actor": "teller-17"},
    ).json()
    rejected = client.post(
        "/payments",
        json=payment_body(debtor_account_id="ACC-1006"),
        headers={"Idempotency-Key": "a-2", "X-Actor": "teller-17"},
    ).json()

    events = client.get("/audit-events").json()

    assert [(e["action"], e["entity_id"]) for e in events] == [
        ("payment.completed", ok["id"]),
        ("payment.rejected", rejected["payment_id"]),
    ]
    assert all(e["actor"] == "teller-17" for e in events)
    assert events[0]["occurred_at"] == "2026-03-16T14:30:00Z"


def test_a_replay_records_no_new_event(client: TestClient) -> None:
    for _ in range(2):
        client.post("/payments", json=payment_body(), headers={"Idempotency-Key": "a-3"})

    assert len(client.get("/audit-events", params={"action": "payment.completed"}).json()) == 1


def test_missing_actor_is_recorded_as_unknown(client: TestClient) -> None:
    client.post("/payments", json=payment_body(), headers={"Idempotency-Key": "a-4"})

    [event] = client.get("/audit-events").json()

    assert event["actor"] == "unknown"
