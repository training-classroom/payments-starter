"""Problem details (RFC 9457) for every error response.

See docs/adr/0002-problem-details-for-errors.md. Every error body has `type`, `title`, `status`,
`detail`, and the machine-readable `code`; `type` is derived from `code`. Status codes:

- 400: the request is malformed (validation, missing header);
- 404: an account or payment doesn't exist;
- 409: an idempotency key was reused for a different request;
- 422: a well-formed payment broke a business rule and was stored as rejected.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from payments.domain.errors import PaymentsError

PROBLEM_TYPE_BASE = "https://problems.payments.example/"
PROBLEM_MEDIA_TYPE = "application/problem+json"


def problem_type(code: str) -> str:
    return PROBLEM_TYPE_BASE + code.replace("_", "-")


def problem_response(
    *,
    status: int,
    code: str,
    title: str,
    detail: str,
    headers: dict[str, str] | None = None,
    **extensions: Any,
) -> JSONResponse:
    body = {
        "type": problem_type(code),
        "title": title,
        "status": status,
        "detail": detail,
        "code": code,
        **extensions,
    }
    return JSONResponse(body, status_code=status, media_type=PROBLEM_MEDIA_TYPE, headers=headers)


async def _payments_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, PaymentsError)
    return problem_response(status=exc.status, code=exc.code, title=exc.title, detail=exc.detail)


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [{"location": list(error["loc"]), "message": error["msg"]} for error in exc.errors()]
    return problem_response(
        status=400,
        code="validation_error",
        title="Invalid request",
        detail="The request body or headers failed validation.",
        errors=errors,
    )


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = "not_found" if exc.status_code == 404 else "http_error"
    return problem_response(
        status=exc.status_code, code=code, title=str(exc.detail), detail=str(exc.detail)
    )


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(PaymentsError, _payments_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
