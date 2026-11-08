# ABUTRON private MCP gateway (outbound tunnel)

**2026-11-08 STATUS: STAGED FOR REVIEW; NOT INSTALLED ON PRODUCTION.**

This is a customer-operated Desktop Commander local stdio MCP server plus an outbound OpenAI Secure MCP Tunnel. **It bypasses the Desktop Commander hosted remote relay and monthly call allowance**, but the OpenAI tunnel control plane is hosted by OpenAI; this is *not* a wholly customer-owned transport.

The local server on Ubuntu is /opt/abutron-dcmcp/node_modules/@wonderwhy-er/desktop-commander/dist/index.js. The host operator has shown that the package and /usr/local/sbin/abutron-dcmcp exist. The host's Node.js is v18.19.1, which does not meet the intended isolated runtime >=22.12. Do not change the global Node installation because APEX services may depend on it.

## Absolute prerequisites (all gated)

1. Preserve a new verified encrypted offsite Restic backup, DB readback, isolated restore evidence, and rollback. Never mark these as done based solely on historical logs.
2. Review source and signed/verified official archives before installing an **isolated** Node >=22.12 at /opt/abutron-mcp/node/bin/node. Do not use curl-pipe-shell, npm latest, or unverified binaries. Review official Node download checksums/signatures and record the pinned build.
3. Verify the official OpenAI [tunnel-client releases](https://github.com/openai/tunnel-client/releases) and install the chosen verified executable root-owned mode 0755 at /usr/local/bin/tunnel-client. Check tunnel-client help quickstart.
4. In [OpenAI Platform tunnel settings](https://platform.openai.com/), create a tunnel and an appropriately scoped runtime API key: Tunnels Read + Use for runtime; Read + Manage only for the administrator. Associate tunnel with the actual ChatGPT workspace. **Never paste API keys into ChatGPT or GitHub.**
5. A ChatGPT **Business or Enterprise/Edu** account with custom full MCP permission is required to execute write-capable custom MCP from the browser. Plus is not supported. A running tunnel is not proof of browser access.

## Review and install (root operator only)

After reviewing a pinned commit from the private abutron-ops repository, copy the script into a **root-owned** checkout path, then use the root console directly. Do not execute untrusted branch code via the GitHub self-hosted runner.

    cd /root/abutron-ops
    git rev-parse HEAD
    bash -n ops/mcp_gateway/abutron-mcp-tunnel.sh
    bash ops/mcp_gateway/abutron-mcp-tunnel.sh preflight
    bash ops/mcp_gateway/abutron-mcp-tunnel.sh stage

Stage creates only an inactive systemd unit at /etc/systemd/system/abutron-mcp-tunnel.service and an isolated launcher at /usr/local/sbin/abutron-dcmcp-isolated. It opens **no inbound ports**, does not restart existing services, and never enables the unit automatically.

Then configure locally (requires real tunnel ID, no key in shell arguments):

    bash ops/mcp_gateway/abutron-mcp-tunnel.sh configure tunnel_REPLACE_WITH_REAL_ID
    bash ops/mcp_gateway/abutron-mcp-tunnel.sh doctor

Review the doctor's results. Only after a passing diagnostic and explicit production approval, enable:

    bash ops/mcp_gateway/abutron-mcp-tunnel.sh enable
    systemctl status abutron-mcp-tunnel.service --no-pager
    journalctl -u abutron-mcp-tunnel.service -n 30 --no-pager

The systemd unit runs as **root**. This is intentional to satisfy the owner's production-admin requirement but is a very high-impact capability. Apply ChatGPT explicit user confirmations, workspace access controls and credential isolation. It cannot be treated as a safe public terminal. Never enable live broker trading, change risk limits or bypass broker checks merely because the tunnel works.

## ChatGPT browser connection

Eligible workspace → Plugins → + → Add custom MCP server → Connection: Tunnel → choose existing tunnel ID → review auth/security → create plugin. Then test actual tools: tools/list, a read-only whoami/hostname command, and required confirmation behavior. **Do not claim working ChatGPT admin until a real tool call succeeds.**

## Rollback

    bash ops/mcp_gateway/abutron-mcp-tunnel.sh rollback

Rollback stops/disables the new tunnel unit and removes its unit + wrapper. Revoke runtime key and tunnel association separately at OpenAI Platform if retiring access. The profile and local key are retained for controlled revocation, not silently deleted.

## Unchanged in this change

Production MT5 services, Deriv and FP Markets execution, APEX, CRM, GitHub runner labels/sudoers, Docker, existing proxy, and all inbound firewall rules. No LIVE trading activation.

## Verification evidence to attach after executing

- Fresh Restic snapshot identifier, repository check, DB readback and isolated restore proof.
- Isolated Node and tunnel-client binary version + SHA256 provenance.
- Bash preflight, doctor output, service status, logs with secrets redacted.
- ChatGPT plugin discovered tool list and read-only command result.
- Explicit high-risk change confirmation and rollback test.

Official docs: https://developers.openai.com/api/docs/guides/secure-mcp-tunnels and https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt
