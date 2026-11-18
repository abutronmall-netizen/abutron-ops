# ABUTRON automation — source coverage and recoverability

Live Ubuntu evidence: **181 distinct executable/source references** across 389 in-scope unit definitions on 18 November 2026. The complete, sanitized list is [worker-source-registry.json](inventory/worker-source-registry.json), including executable basenames, SHA-256, byte size when accessible, and usage categories.

**These 181 source files have NOT all been transferred to GitHub.** A registry and SHA cannot reconstruct a lost worker. The public transfer currently supplies metadata, a read-only inventory builder and blueprint. Exactly seven live unit mappings have an identified counterpart in the separately reviewed V9 source transfer.

## Existing code on GitHub

[ABUTRON-FX-V9/ops/issue25](https://github.com/abutronmall-netizen/ABUTRON-FX-V9/tree/main/ops/issue25) provides ten audited Python source copies, fourteen systemd unit/timer texts, tests, and source hash manifest. Three review files intentionally differ from installed binaries to remove private login/profile literals; use staged compatibility checks before deploying.

Further work lives in V9 PRs #30–#34, which are review/source changes, not production deployments or complete source custody.

## Explicitly missing from PUBLIC GitHub

Raw script bodies of other installed workers, their complete production unit texts, environment values, private account/owner roster, native receipts, HCC/market cache, broker history, SQLite, signing secrets, certificates and backup/recovery keys. Also absent are complete native build attestations, full database schema dump, pinned server packages and an independently verified full disaster restore.

## Required to make this genuinely recoverable

- Create an actually **private, access-controlled** source repository. The connected GitHub repos (including abutron-ops) were observed as public, despite an older README calling abutron-ops private.
- Individually inventory the installed script's exact path, source hash, original code, upstream commit, service+timer, imports, configuration keys, dependencies and security class. Exclude secrets or replace with tested secure configuration.
- Preserve code in logical modules: broker workers; APEX order/exposure; V9 training; CRM/admin/client; native history/equity; audit/reconciliation; backup/recovery; infrastructure.
- Run per-file secret/privacy review and unit/integration tests before publishing even to private storage.
- Commit deployment/rollback manifests and separately validate encrypted offsite recovery and actual source restoration. Keep account-bound historical broker evidence in private encrypted custody rather than public Git.

**Source SHA recorded != source bytes preserved != rollback verified.**
