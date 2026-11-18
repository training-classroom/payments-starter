"""Service settings, read from environment variables prefixed with `PAYMENTS_`.

`PAYMENTS_TIERS` replaces the whole tier table, so it must be a JSON object with every tier, for
example `{"standard": {"max_payment_minor": 300000}, ...}`.
"""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TierPolicy(BaseModel):
    """Limits that apply to every account on one tier. Amounts are minor units (cents)."""

    max_payment_minor: int = Field(gt=0, description="Largest single outbound payment.")


def default_tiers() -> dict[str, TierPolicy]:
    return {
        "standard": TierPolicy(max_payment_minor=250_000),
        "premium": TierPolicy(max_payment_minor=1_000_000),
        "business": TierPolicy(max_payment_minor=5_000_000),
    }


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PAYMENTS_")

    database_url: str = "sqlite:///./payments.db"
    seed_on_startup: bool = True
    tiers: dict[str, TierPolicy] = Field(default_factory=default_tiers)

    def policy_for(self, tier: str) -> TierPolicy:
        """Return the policy for a tier. Every account's tier must be configured."""
        try:
            return self.tiers[tier]
        except KeyError as exc:
            raise LookupError(f"No tier policy is configured for tier {tier!r}") from exc
