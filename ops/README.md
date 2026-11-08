# ABUTRON reviewed inactive-source staging V1

**Status: code review + offline tests only.** These instructions require a separate root operator with authenticated access to \`localhost\`. The GitHub connector cannot install root programs or attest offsite Restic restore by itself. Never change LIVE/DEMO trading switches to enable this.

## What the two programs do

The same Python source \`ops/approved_source_stage_v1.py\` must be installed as root-owned executables using these *exact* names:

- \`/usr/local/sbin/abutron-gh-apex-source-stage-v1\`
- \`/usr/local/sbin/abutron-gh-apex-source-rollback-v1\`

The program refuses arguments and anything other than those two entrypoint names. It never calls systemctl, MT5, brokers, CRM or GitHub; and it never writes to /opt, /etc, live terminals or a production database. Stage verifies an independently root-approved exact APEX commit and SHA256 source tarball, a current encrypted offsite Restic repository check, V7 DB readback, an **isolated restore drill**, and root operator review. It rejects unsafe tar paths, symlinks/hardlinks, unexpected source paths, oversized contents, duplicate entries, mismatched hashes, unsafe root-owned file permissions, stale approval and repeated release installation. It writes only to \`/var/lib/abutron-apex11-inactive-source-v1/releases/\` and source-stage state. Rollback only reverts the INACTIVE staging pointer, retaining staged files as evidence.

Pin: \`abutronmall-netizen/abutron-apex\` at commit \`68f9815d39eeecbecbc5845e051e5ca2f9ae848c\`. Future changes require review and a new pin, not automatic tracking of a moving branch.

## Approval material

A root operator prepares this directory outside the runner-writable workspace:

\`/var/lib/abutron-gh-runner/abutron-apex11-source-approval-v1/\`

Both this directory and its parent must be root-owned and not group/world-writable. Put the independently verified exact source archive at \`source.tar.gz\` (regular root-owned file, no group/world write) and the following **root-owned 0600** manifest at \`manifest.json\`:

\`\`\`json
{
  "schema": "abutron.inactive.source.stage.approval.v1",
  "repo": "abutronmall-netizen/abutron-apex",
  "commit": "68f9815d39eeecbecbc5845e051e5ca2f9ae848c",
  "archive_sha256": "REPLACE_WITH_VERIFIED_64_HEX_SHA256",
  "approved_utc": "REPLACE_WITH_ACTUAL_UTC_ISO8601_Z_WITHIN_SIX_HOURS",
  "restic_snapshot": "REPLACE_WITH_AUTHENTIC_RESTIC_SNAPSHOT_ID",
  "restic_remote_check": "PASS",
  "v7_db_readback": "PASS",
  "isolated_restore_drill": "PASS",
  "root_operator_review": "APPROVED"
}
\`\`\`

**These are not self-certifying strings.** The operator must first perform and retain actual Restic repository/snapshot readback, isolated restore including essential service state and V7 DB readback, accurate source archive provenance, and rollback recovery evidence. Do not set PASS values from past chat messages. No restore drill means STAGING REMAINS BLOCKED. Source archive must consist solely of regular files below \`apex11/abutron_replacement/\`, \`apex11/mql5/\`, \`apex11/tests/\`, or \`risk_guard/\`. No archive extractors, hard links, packages or scripts are executed on the server.

## Bootstrap checklist (not executed by GitHub)

1. Independently verify this script, the pinned APEX commit, actual broker and CRM state, ownership, backup/restore evidence, and read-only tests.
2. Create \`/var/lib/abutron-apex11-inactive-source-v1\` mode 0700 root:root, and protected root-owned approval directory. Ensure the existing parent \`/var/lib/abutron-gh-runner\` is not writable by \`abutrongha\` or others. If it is writable, **stop**; do not weaken checks. Move approval input to a separately reviewed root-only parent and revise/test the code first.
3. Root-install the reviewed file to the **two exact command paths** root:root mode 0750. Record file SHA256 and create tested rollback copies of anything replaced. Verify that Python 3 is already available; do not install packages just for this.
4. Only after review, create root-owned \`/etc/sudoers.d/abutron-gh-apex-source-ops-v1\` mode 0440 with the following **no-argument exact-path** grants (and no other commands):

   \`\`\`text
   abutrongha ALL=(root) NOPASSWD: /usr/local/sbin/abutron-gh-apex-source-stage-v1 "", /usr/local/sbin/abutron-gh-apex-source-rollback-v1 ""
   \`\`\`

5. Validate with \`visudo -cf /etc/sudoers.d/abutron-gh-apex-source-ops-v1\` and \`visudo -c\`. Verify that \`sudo -n id\` and \`sudo -n bash\` remain denied for the runner account.
6. Trigger ONLY the owner-controlled GitHub Actions \`stage-approved-source\` workflow on default \`main\`. Confirm root-owned inactive source hash and state. Then test \`rollback-staged-source\` and confirm no \`/opt\`, MT5, CRM, systemd, financial state or account switches changed.
7. Only after root bootstrap and independent operator review should any separate production deployment or MT5 session activation be considered. The source-stage workflow **does not** promote or authorize trade execution.

## Offline tests

On a separate nonproduction environment: \`python3 -m unittest discover -s ops/tests -p 'test_*.py' -v\`. CI uses \`ubuntu-latest\` only; never a self-hosted ABUTRON runner for PR code.

## Current blockers

- 2026-11-08 restricted verifier reported unchanged 11/12 sources with a changed FP native history collector. Live FP patched collector SHA256 \`2e093fd1cd8d6a33419f805ab4337735097685109ee06d9578b4c3d765ce3f8f\` matches the previously verified clock repair. Do not auto-rollback or bless the discrepancy without provenance review.
- Independent isolated Restic full restore was NOT yet verified.
- The actual root command paths and sudoers addition do NOT yet exist. Until installed, workflow stage/rollback options correctly fail closed.
- Native 6207 V4 root guardian and genuine Deriv receipt, FP native history/execution/ledger, plus six failed services remain outstanding. No LIVE trades.
