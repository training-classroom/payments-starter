"""Submitting and reading payments."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from payments import audit
from payments.clock import Clock
from payments.config import Settings
from payments.domain.errors import AccountNotFound, IdempotencyKeyReused, PaymentNotFound
from payments.models import Account, Payment
from payments.repositories import accounts as accounts_repo
from payments.repositories import ledger as ledger_repo
from payments.repositories import payments as payments_repo
from payments.services.payment_rules import DEFAULT_RULES, PaymentContext, Rule, first_violation


@dataclass(frozen=True)
class PaymentRequest:
    debtor_account_id: str
    creditor_account_id: str
    amount_minor: int
    currency: str
    reference: str


@dataclass(frozen=True)
class PaymentOutcome:
    payment: Payment
    # True when the request repeated an earlier one with the same idempotency key.
    replayed: bool

    @property
    def rejected(self) -> bool:
        return self.payment.status == "rejected"


def new_payment_id() -> str:
    return f"PAY-{uuid.uuid4().hex[:16].upper()}"


class PaymentService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        clock: Clock,
        rules: Sequence[Rule] = DEFAULT_RULES,
    ) -> None:
        self._session = session
        self._settings = settings
        self._clock = clock
        self._rules = rules

    def submit(
        self, request: PaymentRequest, *, idempotency_key: str, actor: str
    ) -> PaymentOutcome:
        """Submit a payment: replay it, reject it, or post it.

        A key the debtor already used returns the stored payment (completed or rejected) without
        evaluating anything again. A rejected payment is stored, so a retry gets the same answer.
        """
        existing = payments_repo.find_by_idempotency_key(
            self._session, request.debtor_account_id, idempotency_key
        )
        if existing is not None:
            if not _same_request(existing, request):
                raise IdempotencyKeyReused(
                    f"Idempotency key {idempotency_key!r} was already used by account "
                    f"{request.debtor_account_id} for a different payment."
                )
            return PaymentOutcome(payment=existing, replayed=True)

        debtor = self._account(request.debtor_account_id)
        creditor = self._account(request.creditor_account_id)
        context = PaymentContext(
            debtor=debtor,
            creditor=creditor,
            amount_minor=request.amount_minor,
            currency=request.currency,
            debtor_balance_minor=accounts_repo.balance_minor(self._session, debtor.id),
            policy=self._settings.policy_for(debtor.tier),
        )
        violation = first_violation(context, self._rules)

        now = self._clock.now()
        payment = Payment(
            id=new_payment_id(),
            debtor_account_id=debtor.id,
            creditor_account_id=creditor.id,
            amount_minor=request.amount_minor,
            currency=request.currency,
            reference=request.reference,
            status="completed" if violation is None else "rejected",
            rejection_code=None if violation is None else violation.code,
            rejection_detail=None if violation is None else violation.detail,
            idempotency_key=idempotency_key,
            created_at=now,
        )
        self._session.add(payment)

        if violation is None:
            ledger_repo.post_transfer(
                self._session,
                payment_id=payment.id,
                debtor_account_id=debtor.id,
                creditor_account_id=creditor.id,
                amount_minor=payment.amount_minor,
                description=payment.reference or f"Payment {payment.id}",
                posted_at=now,
            )
            action, details = "payment.completed", {"amount_minor": payment.amount_minor}
        else:
            action, details = "payment.rejected", {"rejection_code": violation.code}

        audit.record(
            self._session,
            occurred_at=now,
            actor=actor,
            action=action,
            entity_type="payment",
            entity_id=payment.id,
            details={**details, "debtor_account_id": debtor.id},
        )
        self._session.commit()
        return PaymentOutcome(payment=payment, replayed=False)

    def get(self, payment_id: str) -> Payment:
        payment = payments_repo.get(self._session, payment_id)
        if payment is None:
            raise PaymentNotFound(f"No payment with id {payment_id}.")
        return payment

    def _account(self, account_id: str) -> Account:
        account = accounts_repo.get(self._session, account_id)
        if account is None:
            raise AccountNotFound(f"No account with id {account_id}.")
        return account


def _same_request(payment: Payment, request: PaymentRequest) -> bool:
    return (
        payment.creditor_account_id == request.creditor_account_id
        and payment.amount_minor == request.amount_minor
        and payment.currency == request.currency
        and payment.reference == request.reference
    )
