from fastapi.testclient import TestClient

from tests.support import payment_body


def post(client: TestClient, key: str | None = "key-1", **overrides: object):
    headers = {"X-Actor": "teller-17"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return client.post("/payments", json=payment_body(**overrides), headers=headers)


def test_a_new_payment_is_created(client: TestClient) -> None:
    response = post(client)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["amount_minor"] == 10_000
    assert response.headers["Location"] == f"/payments/{body['id']}"
    assert "Idempotent-Replayed" not in response.headers


def test_a_replay_returns_200_with_the_original_body(client: TestClient) -> None:
    first = post(client, key="replay-me")
    second = post(client, key="replay-me")

    assert second.status_code == 200
    assert second.headers["Idempotent-Replayed"] == "true"
    assert second.json() == first.json()


def test_a_rule_violation_is_a_422_problem(client: TestClient) -> None:
    response = post(client, key="too-big", amount_minor=260_000)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = response.json()
    assert problem["type"] == "https://problems.payments.example/amount-over-tier-maximum"
    assert problem["code"] == "amount_over_tier_maximum"
    assert problem["title"] == "Amount over tier maximum"
    assert problem["status"] == 422
    assert "2,500.00 USD" in problem["detail"]
    stored = client.get(f"/payments/{problem['payment_id']}").json()
    assert stored["status"] == "rejected"


def test_a_replayed_rejection_is_the_same_problem(client: TestClient) -> None:
    first = post(client, key="blocked", debtor_account_id="ACC-1006")
    second = post(client, key="blocked", debtor_account_id="ACC-1006")

    assert first.status_code == second.status_code == 422
    assert second.headers["Idempotent-Replayed"] == "true"
    assert second.json() == first.json()


def test_reusing_a_key_with_a_different_body_is_a_409(client: TestClient) -> None:
    post(client, key="reused")
    response = post(client, key="reused", amount_minor=99)

    assert response.status_code == 409
    assert response.json()["code"] == "idempotency_key_reused"


def test_the_idempotency_key_header_is_required(client: TestClient) -> None:
    response = post(client, key=None)

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"


def test_an_invalid_body_is_a_400(client: TestClient) -> None:
    response = post(client, amount_minor=0)

    assert response.status_code == 400
    assert response.json()["errors"][0]["location"] == ["body", "amount_minor"]


def test_an_unknown_account_is_a_404(client: TestClient) -> None:
    response = post(client, creditor_account_id="ACC-9999")

    assert response.status_code == 404
    assert response.json()["code"] == "account_not_found"


def test_get_an_unknown_payment_is_a_404(client: TestClient) -> None:
    response = client.get("/payments/PAY-UNKNOWN")

    assert response.status_code == 404
    assert response.json()["code"] == "payment_not_found"
