"""Errors the service layer raises. The API layer maps each one to a problem+json response
(see docs/adr/0002-problem-details-for-errors.md)."""


class PaymentsError(Exception):
    """Base class for errors the API turns into problem details."""

    status: int = 400
    code: str = "bad_request"
    title: str = "Bad request"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class AccountNotFound(PaymentsError):
    status = 404
    code = "account_not_found"
    title = "Account not found"


class PaymentNotFound(PaymentsError):
    status = 404
    code = "payment_not_found"
    title = "Payment not found"


class IdempotencyKeyReused(PaymentsError):
    """The debtor already used this key for a request with a different body."""

    status = 409
    code = "idempotency_key_reused"
    title = "Idempotency key reused"
