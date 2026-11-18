# Changelog

All notable changes to this service are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the service uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.4.0] - 2025-10-02

### Added
- `GET /audit-events`, filtered by `entity_id` or `action`.
- `GET /accounts/{id}/payments`, including rejected payments.

## [1.3.0] - 2025-07-15

### Changed
- Idempotency keys are scoped per debtor account. Two accounts may use the same key; the unique
  constraint is now on (debtor account, key).

## [1.2.0] - 2025-05-06

### Added
- Per-tier maximum for a single payment (`TierPolicy.max_payment_minor`).
- Rejected payments are stored with their rejection code, and a replay returns the same rejection.

## [1.1.0] - 2025-03-25

### Changed
- All timestamps come from the injected clock and are stored as UTC (ADR 0004).

## [1.0.0] - 2025-02-24

### Added
- Accounts, payments, the double-entry ledger, and the audit trail.
- Idempotent `POST /payments` with the `Idempotency-Key` header.
- Problem details for every error (ADR 0002).
