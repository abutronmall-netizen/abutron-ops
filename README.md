# ABUTRON Operations — restricted production runner

Private repository for **fixed, reviewed GitHub Actions operations** on the ABUTRON Ubuntu `localhost` host. This is **not** unrestricted SSH, a general-purpose sudo shell or an MT5 trading controller.

## Existing runner / scope

- Dedicated nonroot OS account: `abutrongha`.
- Runner: `abutron-prod-01-readonly`, required labels `self-hosted, linux, x64, abutron-diagnostics`.
- Existing production root command: `/usr/local/sbin/abutron-gh-apex-staging-verify`. Its corresponding sudoers file is `/etc/sudoers.d/abutron-gh-apex-staging`. **Only the fixed verifier command is currently evidenced as sudo-allowlisted**; earlier wildcard sudo was revoked.
- Existing `.github/workflows/controlled-sudo-staging.yml` and `.github/workflows/readonly-health.yml` are preserved.

## Reviewed operations workflow

`.github/workflows/abutron-reviewed-operations-v1.yml` introduces four literal operation choices. Launch via **Actions → ABUTRON Reviewed Runner Operations V1 → Run workflow → main**. Only repository-owner `abutronmall-netizen`, the original triggering actor, the default `main` ref and this exact repository are accepted.

| Operation | Actual host command / behavior | Capability now |
| --- | --- | --- |
| `verify-host` | Fixed nonsecret, read-only host/systemd/hash commands; verifies root-owned nonwritable sudo policy and nonroot runner identity | Ready |
| `verify-staging` | `sudo -n /usr/local/sbin/abutron-gh-apex-staging-verify` | Ready, **can legitimately fail** on FP clock-collector baseline drift |
| `stage-approved-source` | `sudo -n /usr/local/sbin/abutron-gh-apex-source-stage-v1` (no arguments) | **LOCKED** until a separately reviewed fixed root-owned source-only stager and exact-command sudoers entry have been securely installed |
| `rollback-staged-source` | `sudo -n /usr/local/sbin/abutron-gh-apex-source-rollback-v1` (no arguments) | **LOCKED** until a separately reviewed fixed root-owned rollback program and exact-command sudoers entry have been installed |

For repeatable connector-based smoke tests, only these two owner-created exact-title issues may trigger the *new* workflow: `ABUTRON OPS VERIFY HOST V1`, `ABUTRON OPS VERIFY STAGING V1`. No issue title, body, labels or comments can invoke deployment or rollback. Outputs remain in GitHub Actions logs. Never paste secrets into issues.

**Deployment meaning:** the future stage operation must copy only independently hash-pinned, approved APEX source into protected *inactive* staging after verifying a fresh encrypted offsite backup, exact source and rollback; it must never install an EX5 into active terminals, change CRM ON/OFF, start writer timers, send orders, touch LIVE accounts or change database schema. Production integration and broker-verified DEMO acceptance require a separately approved process. These root programs **have not been installed by this workflow**. The missing commands are deliberate fail-closed controls, not unfinished implicit sudo access.

## Root bootstrap requirements before activating staging/rollback

A privileged operator on the real production host must separately review and install the root-owned, no-argument source stager and rollback programs. Check root ownership, permissions, immutable/pinned input provenance, path traversal and symlink protection, protected staging destination, current offsite backup/readback, exit-on-error, rollback and audit logs. Add only the **two exact full command paths** to `/etc/sudoers.d/` for `abutrongha`, verify with `visudo -cf`, and separately test an unprivileged runner denial for `sudo -n id` / `sudo -n bash`. Do not grant `NOPASSWD: ALL`, arbitrary flags, `sudo sh -c`, shell interpreters, user-supplied artifacts/refs, or wildcard commands.

No such scripts are shipped or auto-installed by the workflow: guessing production file ownership and rollback state would create a root compromise or accidental trading cutover. The current root verifier should not be weakened to make a failing checksum pass.

## Security invariants

- Runner workflows never execute on `pull_request` or `pull_request_target`. No untrusted repository checkout, input-derived shell command or workflow code from a contributor PR is executed on the production host.
- `permissions: {}` grants no GitHub write token for the new workflow. No job receives trading/broker, Restic or CRM credentials.
- Single concurrency group; operations do not overlap, time out after eight minutes or less, and require `main`, owner and original triggering actor.
- Never use GitHub Actions as a route to bypass the native Deriv 6207 DEMO guardian, V7 CRM customer switch, native order writer exclusivity, 0.10/2/3/20 risk constraints or real broker acknowledgment. FP Markets parity requires independent authenticated native evidence. LIVE always stays OFF.
- Staging verification is a quality gate, not permission to deploy. A successful job does not certify a working or profitable trading system.
- Changes to the root sudo scripts, job permissions, triggers or new operations are production-security changes requiring review, prechange backup and rollback. Keep this repo private and minimize write access.

## Latest known verifier note (8 Nov 2026)

The original sudo staging verifier reported `SOURCE_CHECKSUMS_PASS` but blocked an FP native collector drift in `/opt/apex-client-mt5/fpmarkets-history/fp_native_history_collect.py`. Fresh host diagnostics found its SHA256 to be `2e093fd1cd8d6a33419f805ab4337735097685109ee06d9578b4c3d765ce3f8f`, matching the previously recorded clock patch. Review the baseline against the intended patch; do not overwrite the production version simply to silence the verifier. Production systemd was degraded with six failed units in the same snapshot.

## References

- `abutronmall-netizen/abutron-apex` — guarded V4 EA and APEX 1.1 source, currently not promoted to an active broker execution deployment.
- `abutronmall-netizen/abutron-ops` — approved GitHub read-only diagnostics and root staging verification workflow.
