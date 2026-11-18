from fastapi import APIRouter

from payments.api.deps import SessionDep
from payments.domain.errors import AccountNotFound
from payments.models import Account
from payments.repositories import accounts as accounts_repo
from payments.repositories import ledger as ledger_repo
from payments.repositories import payments as payments_repo
from payments.schemas import AccountOut, LedgerEntryOut, PaymentOut

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def list_accounts(session: SessionDep) -> list[AccountOut]:
    return [_account_out(session, account) for account in accounts_repo.list_all(session)]


@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: str, session: SessionDep) -> AccountOut:
    return _account_out(session, _require(session, account_id))


@router.get("/{account_id}/ledger", response_model=list[LedgerEntryOut])
def get_ledger(account_id: str, session: SessionDep) -> list[LedgerEntryOut]:
    _require(session, account_id)
    entries = ledger_repo.entries_for_account(session, account_id)
    return [LedgerEntryOut.model_validate(entry) for entry in entries]


@router.get("/{account_id}/payments", response_model=list[PaymentOut])
def get_payments(account_id: str, session: SessionDep) -> list[PaymentOut]:
    _require(session, account_id)
    payments = payments_repo.list_for_account(session, account_id)
    return [PaymentOut.model_validate(payment) for payment in payments]


def _require(session: SessionDep, account_id: str) -> Account:
    account = accounts_repo.get(session, account_id)
    if account is None:
        raise AccountNotFound(f"No account with id {account_id}.")
    return account


def _account_out(session: SessionDep, account: Account) -> AccountOut:
    return AccountOut(
        id=account.id,
        holder_name=account.holder_name,
        currency=account.currency,
        tier=account.tier,
        status=account.status,
        balance_minor=accounts_repo.balance_minor(session, account.id),
    )
