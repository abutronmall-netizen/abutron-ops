# ABUTRON FX — Live Automation and Worker Blueprint

**Snapshot:** 2026-11-18 18:14 UTC. The inventory comes from the authorized Ubuntu host using read-only systemctl metadata and source file digests. It describes observed worker definitions, with historic architecture included only as context. A relationship below is **not** proof that the whole execution chain is certified.

## 1. System boundaries and current coverage

| Worker family | Units | Role |
|---|---:|---|
| Execution and reconciliation | 77 | APEX dispatcher, native writer, broker ACK, receipts and reconciliation |
| AI and quantitative research | 61 | V9 brain, candidate training, shadow reports, OOS research |
| Market-data and evidence | 48 | Native market history, M5 bars, quotes, hashes and evidence |
| MT5 runtime | 38 | FP/Deriv terminal workers and supporting processes |
| CRM, licensing, client/admin portals | 34 | Customer ON/OFF, identity, license, front-end/API |
| Risk and compliance | 16 | Owner-wide exposure, stop-risk, equity and loss evidence |
| Recovery and backups | 16 | Restic/offsite, database backup, restoration processes |
| Infrastructure operations | 8 | MCP, service monitoring and GitHub runner |
| Legacy and other cross-cutting units | 91 | Historic or unclassified units requiring separate purpose verification |
| **Total** | **389** | **215 services, 172 timers, 2 sockets** |

At snapshot: 159 active, 207 inactive, 19 failed, 4 activating; install states include 151 enabled, 40 disabled, 12 masked, 171 static and 15 transient. Many inactive entries are expected one-shot services; failed entries require examination and should not automatically be restarted.

Each observed unit appears in the nine inventory category JSON files. Its record includes snapshot ID, sanitized name, active/install state, run-as user, hardening flags, schedule where available, installed unit SHA-256, source basename and source SHA-256 when accessible.

## 2. Dependency architecture

    Client/Admin/Operator portals + CRM / licensing
                       |
               Account and owner registry
                       |
    FP Markets / Deriv MT5 terminals and native exports
                       |
          Broker native M5, quotes, history, ACK
                       |
            Identity / freshness / SHA validation
                 /                   \
     Owner exposure/equity         V9 DEMO research
       and stop-risk                causal training
            |                     / chronological OOS
       APEX risk +                 / prospective shadow
       customer activation        / paper candidates
            |
       Candidate + native preflight
            |
       Single-writer broker bridge
            |
       Native MT5 OrderCheck / OrderSend
            |
       Broker result + protective SL/TP
            |
       Native deals, reconciliation, trailing modifications
            |
       Owner evidence status + CRM publication
            |
       Offsite encrypted backup, monitoring and recovery

**This is the intended workflow graph.** Confirm each actual producer/consumer integration independently using native broker evidence, CRM revision ACKs, installed source checksums and up-to-date systemd results.

## 3. Family contracts

**MT5/broker workers:** Maintain separated FP Markets/Deriv account profiles. Emit authenticated native source with account/owner binding, broker symbol, exchange session clock and freshness. A healthy terminal process does not establish a completed order. Account identifiers must remain private.

**Market data workers:** Collect broker-native quote/bar/history, validate 49-feature M5 inputs where appropriate, preserve closed-candle timestamps and reject revised/missing prices rather than interpolating them. Provenance is different from market accuracy.

**V9 brain/research:** Candidate-only isolated learning consumes broker-closed positions and completed native M5; chronological holdout and prospective predictions require causality and immutable source hashes. Candidate creation is not automatic model promotion. LIVE data must not be used as a DEMO substitute when independent provenance is absent.

**CRM/admin/client:** Establish owner/account relationship, licensing, client ON/OFF revision and independently acknowledged activation. HTTP health of a portal alone does not prove MT5 order authorization.

**Risk and execution:** Distinguish owner-wide open stop-risk from the approved **20% portfolio drawdown ceiling**; use independently reconciled native positions, native contract/profit computation and actual equity. An UNKNOWN owner position is not flat. APEX must not infer a broker fill from local OrderSend response; independent ACK, deal, SL/TP and trailing evidence are separate steps. Existing per-trade risk terms remain unchanged by documentation.

**Evidence/feedback:** Preserve immutable original receipt, trade intent, native deal, source SHA, day-start and sampled equity and owner-linked provenance. Missing historical ACK originals or broker-inception records cannot be recovered merely by a new timer. Selected-window history is not lifetime coverage.

**Recovery:** Backup data, source code, pinned models, CRM state, signed evidence and deployment manifests separately. Encrypted offsite transfer needs checksum readback and a tested restore path; a copied archive is not itself proof of recovery.

**Supervision:** systemd scheduled runs, watchdogs, MCP tunnel and reviewed GitHub workflows should expose objective exit status, freshness and durable error evidence. Disabled, masked, stale and failed units must be kept distinguishable.

## 4. Runtime evidence vs claimed completion

- **Observed:** systemd definition and snapshot state of 389 matching units; 181 installed executable/source references; metadata hashes; scheduled timer declarations.
- **Earlier authenticated DEMO staging:** four FP DEMO native sources, four HCC DEMO profiles and five Deriv volatility instruments were validated; this does not authorize trading or certify complete broker-history coverage.
- **Not established by this audit:** all worker jobs successfully execute end-to-end, broker ACK certification, lifetime history, full day-start/peak equity, complete restore test, every MQL5 binary compile, profitable model, LIVE readiness.
- **Publication:** this snapshot does not enable any service, change customer risk, send orders, promote models, or delete backup files.

## 5. Automation event lifecycle

For every worker, track: triggering timer/service, source script SHA, input age and authenticity, account/owner scope, environment, exit code, output schema, downstream dependency, error reason, last success, and rollback/recovery path.

For a safe run, input validation precedes effects. A worker either records verified results or writes an explicit incomplete/error state. Resume from immutable checkpoints; do not rewrite native historical receipts or silently treat missing evidence as a negative trading result.

## 6. Release and rollback

1. Freeze current hashes, unit identities/permissions, account ownership, linked dependencies and encrypted recovery evidence.
2. Compare reviewed GitHub source to installed host. Sanitized review copies are **not necessarily binary-identical** to production originals.
3. Run unit/contract/privacy tests, native MetaEditor compilation for MQL5, and isolated DEMO-only replay of authenticated native sources.
4. Review the narrow PR and integration impacts; verify source drift, customer-authorized risk ceiling and no LIVE change.
5. Make a separate controlled production release only after review, with explicit rollback and broker-side post-release proof.
6. Independently validate CRM/owner exposure, broker-native order chain and restore capability.

**GitHub source merge ≠ service deployment ≠ trading authorization ≠ broker execution certification.**
