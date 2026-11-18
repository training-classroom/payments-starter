from datetime import UTC, datetime

import pytest

from payments.config import TierPolicy
from payments.models import Account
from payments.services.payment_rules import (
    DEFAULT_RULES,
    REJECTION_TITLES,
    PaymentContext,
    first_violation,
)

OPENED = datetime(2025, 1, 6, tzinfo=UTC)


def account(account_id: str, **overrides: str) -> Account:
    fields = {"currency": "USD", "tier": "standard", "status": "active"} | overrides
    return Account(id=account_id, holder_name="Synthetic Test Holder", opened_at=OPENED, **fields)


def context(**overrides: object) -> PaymentContext:
    fields: dict[str, object] = {
        "debtor": account("ACC-1"),
        "creditor": account("ACC-2"),
        "amount_minor": 10_000,
        "currency": "USD",
        "debtor_balance_minor": 50_000,
        "policy": TierPolicy(max_payment_minor=25_000),
    }
    fields.update(overrides)
    return PaymentContext(**fields)  # type: ignore[arg-type]


def test_a_valid_payment_passes_every_rule() -> None:
    assert first_violation(context()) is None


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"creditor": account("ACC-1")}, "same_account"),
        ({"debtor": account("ACC-1", status="blocked")}, "account_not_active"),
        ({"creditor": account("ACC-2", status="closed")}, "account_not_active"),
        ({"creditor": account("ACC-2", currency="EUR")}, "currency_mismatch"),
        ({"amount_minor": 25_001}, "amount_over_tier_maximum"),
        ({"amount_minor": 20_000, "debtor_balance_minor": 19_999}, "insufficient_funds"),
    ],
)
def test_each_rule_rejects_its_case(overrides: dict[str, object], code: str) -> None:
    violation = first_violation(context(**overrides))
    assert violation is not None
    assert violation.code == code


def test_boundaries_are_inclusive() -> None:
    # Exactly the tier maximum and exactly the whole balance are both allowed.
    assert first_violation(context(amount_minor=25_000, debtor_balance_minor=25_000)) is None


def test_the_first_failing_rule_wins() -> None:
    # Over the tier maximum and short of funds: the tier rule runs first.
    violation = first_violation(context(amount_minor=30_000, debtor_balance_minor=1_000))
    assert violation is not None
    assert violation.code == "amount_over_tier_maximum"


def test_every_rejection_code_has_a_title() -> None:
    codes = {"same_account", "account_not_active", "currency_mismatch"}
    codes |= {"amount_over_tier_maximum", "insufficient_funds"}
    assert codes <= REJECTION_TITLES.keys()
    assert len(DEFAULT_RULES) == len(REJECTION_TITLES)
