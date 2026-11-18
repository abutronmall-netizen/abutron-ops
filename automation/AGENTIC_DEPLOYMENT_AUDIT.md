# ABUTRON V9 Agentic Deployment: Merge-to-Host Evidence Audit

**Verified 18 November 2026, approximately 21:10 UTC.** This is a read-only audit of merged source versus the authorized Ubuntu host. It is not a trading deployment or broker-execution certificate.

## GitHub facts

- PR #17 merged into ABUTRON-FX-V9 main on **2026-11-18 20:20:52 UTC**, merge commit **3bc2f1577dfc3a587ff5c2ce64008d9018226a93**.
- Read-only checkout of main at **6b8e5de2088e16f844b1a12eba123d6ae5f4f8ef** contained the AgenticDecisionEngine, brain substrate, agent orchestration, RiskGate, APEX override integration, CRM exposure method and SQLite schema migration.
- ABUTRON_AGENTIC_ENGINE defaults to false in the source config. The deployment guide describes a change to true as agentic decision-route activation. A feature flag alone does not prove authentic broker exposure or authorize a release.

## Ubuntu verified state

- The guide's /opt/abutron-fx-v9 installation path did not exist during inspection.
- No new agentic source or dedicated agentic unit was located in the inspected V9/APEX install paths; the ABUTRON_AGENTIC_ENGINE setting was not found in inspected installed unit configs.
- Existing V9 research and broker-history timers were present, but these do not establish the agentic decision route as active.
- The observed V9 risk audit status was **NOT_CERTIFIED_FOR_NEW_ORDERS**.
- No LIVE trading, service restart, broker order, model promotion, or risk-setting change was performed.

## Critical production certification gap

**1. The merged MT5 worker does not publish exposure certification.** Source inspection of src/abutron/workers/mt5_worker.py shows terminal launch/restart and lifecycle logging, but no verified broker-native position/equity collector and no call to crm.certify_exposure. Repository search found a call to the method only in scripts/validate_live_certification.py, the offline harness.

**2. CRM certification presently trusts caller-supplied flags.** src/abutron/crm/controls.py defines certify_exposure(connection_id, equity, account_currency, native_positions_verified=True) and writes the supplied values to the DB. That method does not itself require a broker receipt, a current native snapshot, a worker identity, a signed evidence digest, or freshness.

**3. The risk engine uses local receipt rows.** src/abutron/db.py recent_open_positions selects OrderReceiptRow records with OPEN/PROTECTED states. A zero-row internal receipt table is not independent proof a broker has no open position. src/abutron/risk/risk_engine.py accepts a truthy native_positions_verified and USD equity, iterates those receipt rows, and does not independently validate a fresh complete account-bound native position set.

**Consequence:** Manually calling certify_exposure with native_positions_verified=True cannot be treated as broker certification. Nor does an offline 17/17 simulation prove the live worker exports the data. This is a missing broker evidence integration, not a call for a new research or model-promotion veto.

## Isolated test result

The two merged agentic test suites, tests/test_agent_system.py and tests/test_agentic_integration.py, passed **36/36** against the checked-out main source in DEMO mode, with a temporary /tmp data root and LIVE trading disabled. This verifies software-level interfaces, not MetaEditor compilation, live broker-native ACKs, a real exposure-certificate publisher, or safe order execution.

## Authoritative worker-to-execution blueprint

    Broker MT5 account/session and full position inventory
             + native equity, currency, source identity
             + timestamp, worker binding, source digest
                     |
          Verify complete account-bound source
                     |
          Reconcile all open positions and native stop risk
                     |
          Persist an evidence-bound, time-bounded certificate
                     |
          Verify complete owner-linked account group
                     |
       V9 AgenticDecisionEngine / RiskGate / risk evidence
                     |
              Single-writer dispatch
                     |
             Native OrderSend result
                     |
           Broker ACK / deals / SLTP / trailing
                     |
           Independent reconciliation and CRM status

## Actions required before a truthful live deployment claim

1. Implement a trusted broker-worker publisher that obtains actual complete account positions (including an explicit verified-flat state), equity, currency and native stop-risk; bind this to broker account, server, session, owner, timestamp and source SHA.
2. Change the CRM certification path to require that verified source rather than a manually supplied boolean. Invalidate stale, partial, wrong-account and mismatched-session snapshots; never convert missing local receipts into native-flat.
3. Add negative tests for stale/absent evidence, another owner's exposure, missing accounts, non-USD unconverted equity, unverified broker risk, and a locally empty but broker-open account.
4. Verify deployment path, exact source/version hashes, MQL5 build, systemd state, feature flag and agentic route. Verify DEMO broker order-to-ACK/SLTP in a separately controlled test before authorizing a LIVE order path.
5. Keep the existing approved account-specific per-trade settings and portfolio ceiling unchanged. Owner-wide open-stop-risk and portfolio drawdown are different measurements.

**Verified:** merged agentic source; 36 passing isolated tests; server has an unverified agentic install and NOT_CERTIFIED_FOR_NEW_ORDERS evidence.

**Not verified:** installed agentic worker, production broker exposure publication, complete native position inventory, fresh owner exposure, new broker-confirmed orders, LIVE deployment.

**Release rule:** GitHub merge is not installation; a user-set certification flag is not independent broker proof; a feature flag is not broker-execution certification.
