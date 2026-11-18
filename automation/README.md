# ABUTRON FX — Automatic Processes & Worker Blueprint

**Point-in-time inventory:** 18 November 2026, 18:14 UTC, from the authorized Ubuntu production host.

This folder is the public-safe operations blueprint. It **does not** contain customer data, account identity files, credentials, production environment values, private terminal evidence, or a restorable copy of every script.

## Files

| File | Contents |
|---|---|
| [BLUEPRINT.md](BLUEPRINT.md) | Platform architecture, automation stages, dependencies and worker responsibilities |
| [AGENTIC_DEPLOYMENT_AUDIT.md](AGENTIC_DEPLOYMENT_AUDIT.md) | Merged agentic engine, current server deployment status and native exposure integration gap |
| [inventory/summary.json](inventory/summary.json) | System-wide snapshot counts and limitations |
| [inventory/](inventory/) | Every in-scope systemd unit, grouped into nine responsibility areas |
| [inventory/worker-source-registry.json](inventory/worker-source-registry.json) | Installed executable/source basenames, SHA-256 hashes and reference counts |
| [SOURCE_COVERAGE.md](SOURCE_COVERAGE.md) | Existing GitHub sources and missing private source custody |
| [RUNBOOK.md](RUNBOOK.md) | Validation, rollback and recoverability checklist |
| [SECURITY_POLICY.md](SECURITY_POLICY.md) | Source sanitization and privacy boundaries |
| [tools/export_worker_inventory.py](tools/export_worker_inventory.py) | Read-only host inventory builder |
| [tools/verify_inventory.py](tools/verify_inventory.py) | Local/CI schema and public privacy checks |

## Verified snapshot

- **389** matching systemd definitions: 215 services, 172 timers, 2 sockets.
- **159 active, 207 inactive, 19 failed, 4 activating** at the time of inspection.
- Install state: enabled 151, disabled 40, masked 12, static 171, transient 15.
- **181 distinct installed executable/source references**, not 181 uploaded source files.
- Seven live unit references map to existing sanitized V9 source reviewed in [ABUTRON-FX-V9/ops/issue25](https://github.com/abutronmall-netizen/ABUTRON-FX-V9/tree/main/ops/issue25).

The catalog covers the named ABUTRON/APEX/FP/Deriv/MT5/restic/runner systemd prefix families only. It does not exhaustively cover unrelated OS services, background programs, scheduled GitHub Actions, or retired hosts.

**Release boundary:** No systemd unit, timer, broker risk control, trading activation, production model or backup policy was modified by this export. Documentation publication is not execution certification.
