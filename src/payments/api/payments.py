from typing import Annotated

from fastapi import APIRouter, Header, Response, status
from fastapi.responses import JSONResponse

from payments.api.deps import ActorDep, PaymentServiceDep
from payments.api.errors import problem_response
from payments.schemas import PaymentCreate, PaymentOut
from payments.services.payment_rules import REJECTION_TITLES
from payments.services.payment_service import PaymentOutcome, PaymentRequest

router = APIRouter(prefix="/payments", tags=["payments"])

IdempotencyKey = Annotated[str, Header(min_length=1, max_length=100)]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PaymentOut,
    responses={
        200: {"description": "Replay of an earlier request with the same idempotency key"},
        422: {"description": "Rejected by a business rule (stored as rejected)"},
    },
)
def submit_payment(
    body: PaymentCreate,
    idempotency_key: IdempotencyKey,
    service: PaymentServiceDep,
    actor: ActorDep,
    response: Response,
) -> PaymentOut | JSONResponse:
    outcome = service.submit(
        PaymentRequest(
            debtor_account_id=body.debtor_account_id,
            creditor_account_id=body.creditor_account_id,
            amount_minor=body.amount_minor,
            currency=body.currency,
            reference=body.reference,
        ),
        idempotency_key=idempotency_key,
        actor=actor,
    )
    headers = {"Idempotent-Replayed": "true"} if outcome.replayed else {}
    if outcome.rejected:
        return _rejection(outcome, headers)

    payment = outcome.payment
    response.headers.update(headers)
    if outcome.replayed:
        response.status_code = status.HTTP_200_OK
    else:
        response.headers["Location"] = f"/payments/{payment.id}"
    return PaymentOut.model_validate(payment)


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: str, service: PaymentServiceDep) -> PaymentOut:
    return PaymentOut.model_validate(service.get(payment_id))


def _rejection(outcome: PaymentOutcome, headers: dict[str, str]) -> JSONResponse:
    payment = outcome.payment
    code = payment.rejection_code or "rejected"
    return problem_response(
        status=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code=code,
        title=REJECTION_TITLES.get(code, "Payment rejected"),
        detail=payment.rejection_detail or "The payment was rejected.",
        headers=headers,
        payment_id=payment.id,
    )
