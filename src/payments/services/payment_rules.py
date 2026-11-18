"""The business rules a payment must pass before it is posted.

Each rule is a small function that looks at a `PaymentContext` and returns a `RuleViolation`, or
`None` when the payment passes. `DEFAULT_RULES` runs in order and the first violation wins, so the
order decides which reason a caller sees when more than one rule fails.

A rejected payment is stored with its rejection code and detail, so a replay of the same request
returns the same rejection. Every code has a title in `REJECTION_TITLES`, which the API uses for the
problem response.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from payments.config import TierPolicy
from payments.domain.money import format_minor
from payments.models import Account

REJECTION_TITLES: dict[str, str] = {
    "same_account": "Debtor and creditor are the same account",
    "account_not_active": "Account not active",
    "currency_mismatch": "Currency mismatch",
    "amount_over_tier_maximum": "Amount over tier maximum",
    "insufficient_funds": "Insufficient funds",
}


@dataclass(frozen=True)
class RuleViolation:
    code: str
    detail: str

    @property
    def title(self) -> str:
        return REJECTION_TITLES[self.code]


@dataclass(frozen=True)
class PaymentContext:
    """Everything a rule may look at. Rules never query the database themselves."""

    debtor: Account
    creditor: Account
    amount_minor: int
    currency: str
    debtor_balance_minor: int
    policy: TierPolicy


Rule = Callable[[PaymentContext], RuleViolation | None]


def accounts_must_differ(ctx: PaymentContext) -> RuleViolation | None:
    if ctx.debtor.id == ctx.creditor.id:
        return RuleViolation("same_account", f"Account {ctx.debtor.id} can't pay itself.")
    return None


def accounts_must_be_active(ctx: PaymentContext) -> RuleViolation | None:
    for account in (ctx.debtor, ctx.creditor):
        if account.status != "active":
            return RuleViolation("account_not_active", f"Account {account.id} is {account.status}.")
    return None


def currency_must_match(ctx: PaymentContext) -> RuleViolation | None:
    for account in (ctx.debtor, ctx.creditor):
        if account.currency != ctx.currency:
            return RuleViolation(
                "currency_mismatch",
                f"Account {account.id} holds {account.currency}; the payment is in {ctx.currency}.",
            )
    return None


def amount_within_tier_maximum(ctx: PaymentContext) -> RuleViolation | None:
    maximum = ctx.policy.max_payment_minor
    if ctx.amount_minor > maximum:
        return RuleViolation(
            "amount_over_tier_maximum",
            f"The {ctx.debtor.tier} tier allows at most {format_minor(maximum, ctx.currency)} "
            "per payment.",
        )
    return None


def sufficient_funds(ctx: PaymentContext) -> RuleViolation | None:
    if ctx.amount_minor > ctx.debtor_balance_minor:
        return RuleViolation(
            "insufficient_funds",
            f"Account {ctx.debtor.id} has {format_minor(ctx.debtor_balance_minor, ctx.currency)} "
            "available.",
        )
    return None


DEFAULT_RULES: tuple[Rule, ...] = (
    accounts_must_differ,
    accounts_must_be_active,
    currency_must_match,
    amount_within_tier_maximum,
    sufficient_funds,
)


def first_violation(
    ctx: PaymentContext, rules: Sequence[Rule] = DEFAULT_RULES
) -> RuleViolation | None:
    for rule in rules:
        violation = rule(ctx)
        if violation is not None:
            return violation
    return None
