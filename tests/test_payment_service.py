import pytest
from sqlalchemy.orm import Session

from payments import audit
from payments.domain.errors import AccountNotFound, IdempotencyKeyReused
from payments.repositories import accounts as accounts_repo
from payments.repositories import ledger as ledger_repo
from payments.services.payment_service import PaymentRequest, PaymentService
from tests.support import FrozenClock


def request(**overrides: object) -> PaymentRequest:
    fields: dict[str, object] = {
        "debtor_account_id": "ACC-1001",
        "creditor_account_id": "ACC-1002",
        "amount_minor": 10_000,
        "currency": "USD",
        "reference": "Invoice 0001",
    }
    fields.update(overrides)
    return PaymentRequest(**fields)  # type: ignore[arg-type]


def test_a_completed_payment_posts_both_ledger_sides(
    service: PaymentService, session: Session
) -> None:
    before_debtor = accounts_repo.balance_minor(session, "ACC-1001")
    before_creditor = accounts_repo.balance_minor(session, "ACC-1002")

    outcome = service.submit(request(), idempotency_key="k-1", actor="tester")

    assert outcome.payment.status == "completed"
    assert not outcome.replayed
    assert accounts_repo.balance_minor(session, "ACC-1001") == before_debtor - 10_000
    assert accounts_repo.balance_minor(session, "ACC-1002") == before_creditor + 10_000
    entries = [e for e in ledger_repo.entries_for_account(session, "ACC-1001") if e.payment_id]
    assert [(e.direction, e.amount_minor) for e in entries] == [("debit", 10_000)]


def test_a_rejected_payment_is_stored_audited_and_not_posted(
    service: PaymentService, session: Session
) -> None:
    before = accounts_repo.balance_minor(session, "ACC-1002")

    # ACC-1002 is standard tier: 2,500.00 per payment.
    outcome = service.submit(
        request(debtor_account_id="ACC-1002", creditor_account_id="ACC-1001", amount_minor=260_000),
        idempotency_key="k-2",
        actor="tester",
    )

    assert outcome.payment.status == "rejected"
    assert outcome.payment.rejection_code == "amount_over_tier_maximum"
    assert accounts_repo.balance_minor(session, "ACC-1002") == before
    events = audit.list_events(session, entity_id=outcome.payment.id)
    assert [e.action for e in events] == ["payment.rejected"]
    assert events[0].details["rejection_code"] == "amount_over_tier_maximum"


def test_timestamps_come_from_the_clock(
    service: PaymentService, session: Session, clock: FrozenClock
) -> None:
    outcome = service.submit(request(), idempotency_key="k-3", actor="tester")

    assert outcome.payment.created_at == clock.now()
    [event] = audit.list_events(session, entity_id=outcome.payment.id)
    assert event.occurred_at == clock.now()
    assert event.actor == "tester"


def test_a_replay_returns_the_stored_payment_without_posting_again(
    service: PaymentService, session: Session
) -> None:
    first = service.submit(request(), idempotency_key="k-4", actor="tester")
    balance_after_first = accounts_repo.balance_minor(session, "ACC-1001")

    second = service.submit(request(), idempotency_key="k-4", actor="tester")

    assert second.replayed
    assert second.payment.id == first.payment.id
    assert accounts_repo.balance_minor(session, "ACC-1001") == balance_after_first


def test_a_replay_of_a_rejected_payment_is_still_rejected(service: PaymentService) -> None:
    rejected = request(debtor_account_id="ACC-1006", creditor_account_id="ACC-1001")
    first = service.submit(rejected, idempotency_key="k-5", actor="tester")

    second = service.submit(rejected, idempotency_key="k-5", actor="tester")

    assert first.rejected and second.rejected
    assert second.replayed
    assert second.payment.id == first.payment.id


def test_reusing_a_key_for_a_different_payment_is_a_conflict(service: PaymentService) -> None:
    service.submit(request(), idempotency_key="k-6", actor="tester")

    with pytest.raises(IdempotencyKeyReused):
        service.submit(request(amount_minor=20_000), idempotency_key="k-6", actor="tester")


def test_keys_are_scoped_to_the_debtor(service: PaymentService) -> None:
    first = service.submit(request(), idempotency_key="shared-key", actor="tester")

    other_debtor = request(debtor_account_id="ACC-1003", creditor_account_id="ACC-1001")
    second = service.submit(other_debtor, idempotency_key="shared-key", actor="tester")

    assert not second.replayed
    assert second.payment.id != first.payment.id


def test_an_unknown_account_is_not_found(service: PaymentService) -> None:
    with pytest.raises(AccountNotFound):
        service.submit(request(creditor_account_id="ACC-9999"), idempotency_key="k-7", actor="t")
