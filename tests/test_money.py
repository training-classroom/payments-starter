import pytest

from payments.domain.money import format_minor


@pytest.mark.parametrize(
    ("amount_minor", "expected"),
    [
        (0, "0.00 USD"),
        (5, "0.05 USD"),
        (250_000, "2,500.00 USD"),
        (123_456_789, "1,234,567.89 USD"),
        (-1_050, "-10.50 USD"),
    ],
)
def test_format_minor(amount_minor: int, expected: str) -> None:
    assert format_minor(amount_minor, "USD") == expected
