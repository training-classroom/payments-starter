"""Request and response bodies. Amounts are integers in minor units."""

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

AccountId = Annotated[str, Field(min_length=1, max_length=20, examples=["ACC-1001"])]
CurrencyCode = Annotated[str, Field(pattern=r"^[A-Z]{3}$", examples=["USD"])]


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    debtor_account_id: AccountId
    creditor_account_id: AccountId
    amount_minor: Annotated[int, Field(gt=0, description="Amount in minor units (cents).")]
    currency: CurrencyCode
    reference: Annotated[str, Field(max_length=140)] = ""


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    debtor_account_id: str
    creditor_account_id: str
    amount_minor: int
    currency: str
    reference: str
    status: str
    rejection_code: str | None
    created_at: datetime


class AccountOut(BaseModel):
    id: str
    holder_name: str
    currency: str
    tier: str
    status: str
    balance_minor: int


class LedgerEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: str | None
    direction: str
    amount_minor: int
    description: str
    posted_at: datetime


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: datetime
    actor: str
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any]
