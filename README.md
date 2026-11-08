# ABUTRON Operations

This private repository hosts a narrow read-only diagnostic bridge for ABUTRON Linode. It is **not** unrestricted SSH access.

## Runner setup
1. In GitHub open **Settings → Actions → Runners → New self-hosted runner** and choose **Linux x64**.
2. On verified production Linode, set up the official GitHub runner using the generated commands, from a dedicated **non-root, non-sudo** Linux account, with directory ownership restricted to that account.
3. Add `--labels abutron-diagnostics` to the GitHub registration command. Choose the name `abutron-prod-01-readonly`. Confirm status **Idle** before testing.
4. Do not paste registration tokens, credentials, SSH keys or broker data into chat.
5. Read the complete GitHub runner security guidance before accepting any changes to this repository's workflows.

## First test
Use the GitHub connector to create an issue in this repository with title exactly `ABUTRON HEALTHCHECK V1` from owner `abutronmall-netizen`. The fixed workflow `.github/workflows/readonly-health.yml` runs seven allowlisted, read-only OS commands and posts an issue comment containing the result. Issue bodies are never executed.

## Security
- Keep the repository **private** with minimal writers; only the repository owner is permitted to request the existing check.
- Never grant the runner sudo, broker credentials, trading service identities, or privileged file permissions.
- The workflow checks only OS metrics; **no automatic trades, deployments, service restarts, or settings changes**.
- Never add `pull_request` triggers to this runner. Treat any workflow changes as production changes requiring independent review.
- Do not trigger a test until server identity, permissions and backup posture have been reviewed.
- The ChatGPT GitHub connector cannot directly SSH into the host; operation runs asynchronously as an Actions job and is read back from the GitHub issue comments.
