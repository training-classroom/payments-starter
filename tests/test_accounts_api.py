from fastapi.testclient import TestClient

from tests.support import payment_body


def test_list_accounts_returns_the_seeded_accounts(client: TestClient) -> None:
    accounts = client.get("/accounts").json()

    assert [a["id"] for a in accounts][:2] == ["ACC-1001", "ACC-1002"]
    assert {a["tier"] for a in accounts} == {"standard", "premium", "business"}


def test_balance_reflects_completed_payments(client: TestClient) -> None:
    before = client.get("/accounts/ACC-1001").json()["balance_minor"]
    client.post("/payments", json=payment_body(), headers={"Idempotency-Key": "bal-1"})

    after = client.get("/accounts/ACC-1001").json()["balance_minor"]

    assert after == before - 10_000


def test_ledger_lists_opening_balance_then_postings(client: TestClient) -> None:
    client.post("/payments", json=payment_body(), headers={"Idempotency-Key": "led-1"})

    ledger = client.get("/accounts/ACC-1002/ledger").json()

    assert [(e["direction"], e["amount_minor"]) for e in ledger] == [
        ("credit", 300_000),
        ("credit", 10_000),
    ]


def test_account_payments_include_rejected_ones(client: TestClient) -> None:
    client.post(
        "/payments",
        json=payment_body(amount_minor=999_999),
        headers={"Idempotency-Key": "rej-1"},
    )

    payments = client.get("/accounts/ACC-1001/payments").json()

    assert [p["status"] for p in payments] == ["rejected"]


def test_an_unknown_account_is_a_404(client: TestClient) -> None:
    assert client.get("/accounts/ACC-0000").status_code == 404
