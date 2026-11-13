# Three ABUTRON Portal Flows

## CLIENT-FLOW

Register -> verify email -> authenticate -> license/subscription -> connect approved MT5 broker account -> broker-native verification -> user requests account trading ON/OFF -> server confirms effective state -> view signals, open positions, account performance, notifications, billing, and support.

Current API examples: `/account/api/client/me`, `/connections`, `/trading-controls`, `/license/summary`, `/ai-engine`, `/runtime-health`. Actual user ON request and effective execution state are separate.

## ADMIN-FLOW

Authenticate as Superadmin -> verify email MFA -> inspect CRM accounts and licenses -> inspect subscriptions, broker links, risk and audit evidence -> operational workflow and support. Mutating roles, payments and account permissions require separate audited server-side endpoints and cannot be inferred from existing read-only API.

Current API examples: `/account/api/client/admin/me`, `/overview`, `/mfa/request`, `/mfa/verify`, `/runtime-health`.

## APEX-FLOW

Authenticated broker feed -> normalized M5/M15/H1 market data -> APEX 1.1 directional signal -> de-duplication and conviction ranking -> account-bound risk/admission -> one authorized native order writer -> MT5 order check/send -> authentic broker acknowledgment -> protected SL/TP -> position lifecycle -> reconciliation and journal -> portal telemetry.

Operator endpoints include `/api/apex11-engines`, `/api/apex11-broker-evidence`, `/api/runtime-health`, `/api/overview`, `/api/scanner`, `/api/risk-governor` and `/api/order-prechecks`. Research publisher liveness is not proof of trading.

## Cross-portal authority

- Client: customer-owned intent and visibility.
- Admin: CRM and commercial entitlements, with audited operator roles.
- APEX: technical engine observability, market signals and native broker-execution evidence.

All three consume backend authoritative account identifiers, licenses, execution intents, broker receipts and risk snapshots. Distinguish `desired_on` from `effective_on`; distinguish `publisher_healthy` from `order_accepted_by_broker`; do not display offline data as fresh. Protect live environment separately and preserve account ON/OFF controls, stop protections, and portfolio ceiling.
