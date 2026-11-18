"""Checks that keep the code in line with the ADRs in docs/adr/."""

import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src" / "payments"


def python_files() -> list[Path]:
    return sorted(SOURCE.rglob("*.py"))


def test_only_the_clock_reads_the_current_time() -> None:
    # ADR 0004: everything else gets the time from the injected Clock.
    pattern = re.compile(r"datetime\.(now|utcnow|today)\(|date\.today\(|time\.time\(")
    offenders = [
        path.relative_to(SOURCE).as_posix()
        for path in python_files()
        if path.name != "clock.py" and pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_amounts_are_never_floats_or_decimals() -> None:
    # ADR 0001: amounts are integers in minor units.
    pattern = re.compile(r"\bfloat\(|\bDecimal\b|: float\b|-> float\b")
    offenders = [
        path.relative_to(SOURCE).as_posix()
        for path in python_files()
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
