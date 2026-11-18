diff --git a/automation/BLUEPRINT.md b/automation/BLUEPRINT.md
index 3e6ec53..1d66a03 100644
--- a/automation/BLUEPRINT.md
+++ b/automation/BLUEPRINT.md
@@ -2,6 +2,8 @@
 
 **Snapshot:** 2026-11-18 18:14 UTC. The inventory comes from the authorized Ubuntu host using read-only systemctl metadata and source file digests. It describes observed worker definitions, with historic architecture included only as context. A relationship below is **not** proof that the whole execution chain is certified.
 
+**Agentic layer (updated):** Section 3 documents the agentic hybrid multi-agent decision layer merged to `ABUTRON-FX-V9` `main` (PR #17, 2026-11-18 20:20 UTC) as the new primary operating layer that overrides APEX. This is a **source-level** addition; the agentic engine is **not yet deployed or verified on the host** as of the snapshot above, so it does not appear in the observed unit inventory.
+
 ## 1. System boundaries and current coverage
 
 | Worker family | Units | Role |
@@ -32,15 +34,20 @@ Each observed unit appears in the nine inventory category JSON files. Its record
           Broker native M5, quotes, history, ACK
                        |
             Identity / freshness / SHA validation
-                 /                   \
+                 /                     \
      Owner exposure/equity         V9 DEMO research
        and stop-risk                causal training
             |                     / chronological OOS
-       APEX risk +                 / prospective shadow
-       customer activation        / paper candidates
+   AGENTIC decision engine      / prospective shadow
+   (sense -> think -> gate)    / paper candidates
+   brain = signal authority
+            |
+       RiskGate (unbypassable) + exposure guard
             |
        Candidate + native preflight
             |
+       (APEX legacy — bypassed when agentic active)
+            |
        Single-writer broker bridge
             |
        Native MT5 OrderCheck / OrderSend
@@ -55,7 +62,50 @@ Each observed unit appears in the nine inventory category JSON files. Its record
 
 **This is the intended workflow graph.** Confirm each actual producer/consumer integration independently using native broker evidence, CRM revision ACKs, installed source checksums and up-to-date systemd results.
 
-## 3. Family contracts
+## 3. Agentic multi-agent decision layer (primary operating layer)
+
+ABUTRON FX V9 now ships an **agentic hybrid multi-agent system** as the **primary operating layer**. The vendored APEX engine is **legacy** — the agentic engine overrides it as the decision authority. This layer is merged to `ABUTRON-FX-V9` `main` (PR #17) but is **not yet deployed/verified on the host** as of this snapshot; the deployment steps below are the activation action.
+
+### 3.1 Decision engine and override switch
+
+The decision path is controlled by one environment flag:
+
+| Flag | Default | Effect |
+|---|---|---|
+| `ABUTRON_AGENTIC_ENGINE` | `false` | `true` activates the agentic decision path and **overrides APEX** in `ApexIntegration.process_candle`. APEX is bypassed entirely. |
+
+When `ABUTRON_AGENTIC_ENGINE=true`, `process_candle()` routes through `_run_agentic_decision()` **before** the APEX availability check, so the agentic engine does not depend on the vendored APEX source. Setting the flag is the deployment action that makes the agentic system the live decision authority — there is **no staging/certification veto** that holds it in shadow (the validation harnesses are tools, not runtime gates). Rollback to APEX: set `ABUTRON_AGENTIC_ENGINE=false` and restart the portal + dispatcher.
+
+### 3.2 Architecture (sense → think → gate → act → monitor → recover)
+
+The `AgenticDecisionEngine` (`ABUTRON-FX-V9` `src/abutron/agent/production.py`) composes specialized sub-agents around the trained unified brain (`data/brains/unified_m5/nexus_brain.json`) as the **signal authority**:
+
+- **Signal agent** — brain-derived signal authority (the deep + self-learning component; MLP + `online_learn`).
+- **Orchestrator** — composes the decision pass across agents.
+- **Risk agent / RiskGate** — the **unbypassable** deterministic money-safety gate; delegates to the V9 `RiskGuard`.
+- **Execution agent** — produces gate-approved candidates.
+- **Monitoring / Recovery agents** — observe outcomes and drive recovery.
+
+Agents and workers remain **deterministic and auditable**; the brain predicts direction, the RiskGate validates money-safety. Optional LLM reasoning / debate layers (`ABUTRON_GEMMA_ENABLED`, `ABUTRON_DEBATE_ENABLED`) are advisory and never sit on the order path.
+
+### 3.3 Unbypassable safety invariants
+
+These are enforced regardless of deployment mode and are **not** removed by the override:
+
+- Per-trade risk: 0.15% of equity (`ABUTRON_PER_TRADE_PCT`).
+- Portfolio ceiling: 20% aggregate stop-risk (`ABUTRON_RISK_CAP_PCT`).
+- Reward:risk floor: R:R ≥ 1.50.
+- Max position: 50 lots.
+- Exposure certification: the dispatcher blocks (`BLOCKED_INCOMPLETE_EXPOSURE`) until a broker worker sets `native_positions_verified` + `equity` + `account_currency=USD` from broker-native evidence.
+- At-most-once: the replay-key unique constraint prevents duplicate order submission for the same candle.
+- Fail-closed: no candidate when the gate rejects or the brain signal is weak; UNKNOWN receipts block resubmission until reconciliation.
+
+### 3.4 Deployment status
+
+- **Merged to source:** agentic engine, APEX override wiring, exposure-certification schema (`db.py` / `crm.certify_exposure`), RiskGate, and `docs/DEPLOYMENT.md` are on `ABUTRON-FX-V9` `main`.
+- **Not yet verified on host:** the agentic engine is **not** confirmed running on the Ubuntu server. Activation requires setting `ABUTRON_AGENTIC_ENGINE=true` in the portal + dispatcher units (see `ABUTRON-FX-V9/docs/DEPLOYMENT.md` §3), connecting a DEMO broker, and certifying exposure. Verify with `scripts/validate_live_certification.py` (17/17) and broker-side post-release proof.
+
+## 4. Family contracts
 
 **MT5/broker workers:** Maintain separated FP Markets/Deriv account profiles. Emit authenticated native source with account/owner binding, broker symbol, exchange session clock and freshness. A healthy terminal process does not establish a completed order. Account identifiers must remain private.
 
@@ -65,7 +115,7 @@ Each observed unit appears in the nine inventory category JSON files. Its record
 
 **CRM/admin/client:** Establish owner/account relationship, licensing, client ON/OFF revision and independently acknowledged activation. HTTP health of a portal alone does not prove MT5 order authorization.
 
-**Risk and execution:** Distinguish owner-wide open stop-risk from the approved **20% portfolio drawdown ceiling**; use independently reconciled native positions, native contract/profit computation and actual equity. An UNKNOWN owner position is not flat. APEX must not infer a broker fill from local OrderSend response; independent ACK, deal, SL/TP and trailing evidence are separate steps. Existing per-trade risk terms remain unchanged by documentation.
+**Risk and execution:** Distinguish owner-wide open stop-risk from the approved **20% portfolio drawdown ceiling**; use independently reconciled native positions, native contract/profit computation and actual equity. An UNKNOWN owner position is not flat. The **agentic decision engine** is the primary decision authority (when `ABUTRON_AGENTIC_ENGINE=true`); the unbypassable **RiskGate** enforces the hard invariants before any candidate is produced, and the dispatcher blocks on uncertified exposure. APEX is legacy and bypassed in agentic mode; it must not infer a broker fill from local OrderSend response — independent ACK, deal, SL/TP and trailing evidence are separate steps. Existing per-trade risk terms remain unchanged by documentation.
 
 **Evidence/feedback:** Preserve immutable original receipt, trade intent, native deal, source SHA, day-start and sampled equity and owner-linked provenance. Missing historical ACK originals or broker-inception records cannot be recovered merely by a new timer. Selected-window history is not lifetime coverage.
 
@@ -73,26 +123,27 @@ Each observed unit appears in the nine inventory category JSON files. Its record
 
 **Supervision:** systemd scheduled runs, watchdogs, MCP tunnel and reviewed GitHub workflows should expose objective exit status, freshness and durable error evidence. Disabled, masked, stale and failed units must be kept distinguishable.
 
-## 4. Runtime evidence vs claimed completion
+## 5. Runtime evidence vs claimed completion
 
 - **Observed:** systemd definition and snapshot state of 389 matching units; 181 installed executable/source references; metadata hashes; scheduled timer declarations.
 - **Earlier authenticated DEMO staging:** four FP DEMO native sources, four HCC DEMO profiles and five Deriv volatility instruments were validated; this does not authorize trading or certify complete broker-history coverage.
 - **Not established by this audit:** all worker jobs successfully execute end-to-end, broker ACK certification, lifetime history, full day-start/peak equity, complete restore test, every MQL5 binary compile, profitable model, LIVE readiness.
 - **Publication:** this snapshot does not enable any service, change customer risk, send orders, promote models, or delete backup files.
 
-## 5. Automation event lifecycle
+## 6. Automation event lifecycle
 
 For every worker, track: triggering timer/service, source script SHA, input age and authenticity, account/owner scope, environment, exit code, output schema, downstream dependency, error reason, last success, and rollback/recovery path.
 
 For a safe run, input validation precedes effects. A worker either records verified results or writes an explicit incomplete/error state. Resume from immutable checkpoints; do not rewrite native historical receipts or silently treat missing evidence as a negative trading result.
 
-## 6. Release and rollback
+## 7. Release and rollback
 
 1. Freeze current hashes, unit identities/permissions, account ownership, linked dependencies and encrypted recovery evidence.
 2. Compare reviewed GitHub source to installed host. Sanitized review copies are **not necessarily binary-identical** to production originals.
 3. Run unit/contract/privacy tests, native MetaEditor compilation for MQL5, and isolated DEMO-only replay of authenticated native sources.
 4. Review the narrow PR and integration impacts; verify source drift, customer-authorized risk ceiling and no LIVE change.
-5. Make a separate controlled production release only after review, with explicit rollback and broker-side post-release proof.
-6. Independently validate CRM/owner exposure, broker-native order chain and restore capability.
+5. Activate the agentic decision layer as the controlled release action: set `ABUTRON_AGENTIC_ENGINE=true` in the portal + dispatcher units, restart, and confirm the agentic engine is the live decision authority (APEX bypassed). Rollback to APEX: set `ABUTRON_AGENTIC_ENGINE=false` and restart. The RiskGate + exposure guard remain unbypassable in either mode.
+6. Make a separate controlled production release only after review, with explicit rollback and broker-side post-release proof.
+7. Independently validate CRM/owner exposure, broker-native order chain and restore capability.
 
 **GitHub source merge ≠ service deployment ≠ trading authorization ≠ broker execution certification.**
diff --git a/automation/RUNBOOK.md b/automation/RUNBOOK.md
index 3e8dea9..b4fe9bc 100644
--- a/automation/RUNBOOK.md
+++ b/automation/RUNBOOK.md
@@ -27,6 +27,8 @@ Use a dedicated DEMO-only data directory, restricted systemd service account, Pr
 
 No LIVE activation, model promotion or risk-limit change is implied by source transfer. For MQL5 executable changes, require native MetaEditor compile and broker-confirmed DEMO evidence. For V9 research, require causal input features, independent chronological holdout, and isolated candidate comparisons.
 
+**Agentic decision layer activation:** the agentic engine (merged to `ABUTRON-FX-V9` `main`) becomes the live decision authority only when `ABUTRON_AGENTIC_ENGINE=true` is set in the portal + dispatcher units and the services are restarted (see `ABUTRON-FX-V9/docs/DEPLOYMENT.md` §3). This is the controlled release action that overrides legacy APEX; the RiskGate + exposure guard remain unbypassable. Rollback: set `ABUTRON_AGENTIC_ENGINE=false` and restart. Confirm agentic authority and broker-native order-chain proof before treating the deployment as live.
+
 ## Recovery
 
 Preserve original scripts, private terminal profiles, license/CRM databases, operational receipts, manifest, restore instructions and encrypted offsite snapshots in approved private custody. Confirm remote SHA readback and independently test restore when feasible. Do not delete backup source files until destination readback and the recovery plan are verified.
