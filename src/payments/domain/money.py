"""Money helpers.

Amounts are integers in minor units (cents for USD and EUR) everywhere in the service: in the API,
in the database, and in calculations (see docs/adr/0001-money-in-integer-minor-units.md). No float
or decimal type ever holds an amount; this module only formats amounts for people to read.
"""

SUPPORTED_CURRENCIES = frozenset({"USD", "EUR"})

# Both supported currencies have two decimal places.
_MINOR_DIGITS = 2


def format_minor(amount_minor: int, currency: str) -> str:
    """Format an amount for messages, e.g. `format_minor(250000, "USD")` -> `"2,500.00 USD"`."""
    sign = "-" if amount_minor < 0 else ""
    major, minor = divmod(abs(amount_minor), 10**_MINOR_DIGITS)
    return f"{sign}{major:,}.{minor:0{_MINOR_DIGITS}d} {currency}"
