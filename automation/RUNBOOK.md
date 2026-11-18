# ABUTRON FX — Worker operations, validation and recovery

All steps below are **read-only** and operate on the authorized Ubuntu host, not from GitHub Actions with broad shell privileges.

## Inspect live jobs and timers

- Run: **systemctl list-unit-files --all --no-pager**
- Run: **systemctl list-timers --all --no-pager**
- Run: **systemctl --failed --no-pager**
- For one reviewed worker: **systemctl show UNIT.service -p User -p ActiveState -p Result -p ProtectSystem -p NoNewPrivileges -p PrivateNetwork -p ReadWritePaths**
- For recent failures: **sudo journalctl -u UNIT.service --since "2 hours ago" --no-pager**
- Compare installed worker file: **sudo sha256sum /path/to/authorized/worker-script**

Replace UNIT with the local actual systemd name. The PUBLIC catalog may hide connection profiles; journal output and full unit texts may contain secrets and must not be uploaded.

## Health vs execution

A timer being enabled is not proof it ran successfully, and systemd active state is not a broker-native fill. The snapshot recorded **19 failed units**; classify them as legacy QA, one-shot compilation or current operational blockers rather than mass-restarting. Check source age, owner/account scope, recent service error, broker history, CRM revision, and writer ACK separately.

## Refresh the inventory without changing services

Run the reviewed **tools/export_worker_inventory.py** locally on Ubuntu with read-only systemctl access. This generates a candidate metadata snapshot under /tmp. Review and scrub source labels and identity fields, then run **tools/verify_inventory.py** against the prepared public directory. Publishing must be a separate reviewed PR; no automatic CI job should collect host secrets.

## Isolated staging and production release

Use a dedicated DEMO-only data directory, restricted systemd service account, ProtectSystem=strict, NoNewPrivileges=yes, network isolation when source access permits, and **no OrderSend/writer authority**. Verify broker-native source identity, exact source SHA, account mapping, unit permissions, market-data freshness, risk proof, test results and rollback before considering deployment.

No LIVE activation, model promotion or risk-limit change is implied by source transfer. For MQL5 executable changes, require native MetaEditor compile and broker-confirmed DEMO evidence. For V9 research, require causal input features, independent chronological holdout, and isolated candidate comparisons.

**Agentic decision layer activation:** the agentic engine (merged to `ABUTRON-FX-V9` `main`) becomes the live decision authority only when `ABUTRON_AGENTIC_ENGINE=true` is set in the portal + dispatcher units and the services are restarted (see `ABUTRON-FX-V9/docs/DEPLOYMENT.md` §3). This is the controlled release action that overrides legacy APEX; the RiskGate + exposure guard remain unbypassable. Rollback: set `ABUTRON_AGENTIC_ENGINE=false` and restart. Confirm agentic authority and broker-native order-chain proof before treating the deployment as live.

## Recovery

Preserve original scripts, private terminal profiles, license/CRM databases, operational receipts, manifest, restore instructions and encrypted offsite snapshots in approved private custody. Confirm remote SHA readback and independently test restore when feasible. Do not delete backup source files until destination readback and the recovery plan are verified.

When a source hash drifts: STOP replacement, determine if a reviewed deployment occurred, compare to manifest, inventory dependent services and retain previous known-good version. This registry alone is **not** a restorable snapshot of the server.
