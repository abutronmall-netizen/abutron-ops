# ABUTRON — Finish private remote MCP tunnel (operator-only)

**Verified Ubuntu localhost as of 2026-11-08:**

- Desktop Commander 0.3.1 stdio MCP initialization PASSED, tools/list discovered 25 tools (read-only [run 42483971911](https://github.com/abutronmall-netizen/abutron-ops/actions/runs/42483971911)).
- Isolated Node 22.23.4 available to non-root (repair [run 42483933700](https://github.com/abutronmall-netizen/abutron-ops/actions/runs/42483933700)).
- Official OpenAI Linux AMD64 tunnel-client v0.0.20 installed at `/usr/local/bin/tunnel-client` using verified release SHA256, confirmed `help quickstart` (run [42485169933](https://github.com/abutronmall-netizen/abutron-ops/actions/runs/42485169933)).
- New outbound-only tunnel service staged as `/etc/systemd/system/abutron-mcp-tunnel.service`, **disabled/inactive**, under distinct unprivileged `abutronmcp` user (run [42485578869](https://github.com/abutronmall-netizen/abutron-ops/actions/runs/42485578869)).
- **Not connected:** OpenAI Platform tunnel ID and runtime key have not been configured. A service without those cannot connect to OpenAI. An active tunnel does not grant this ChatGPT Plus session custom MCP access.

## Required user-owned OpenAI Platform account step

Visit [Platform Tunnels settings](https://platform.openai.com/settings/organization/tunnels) and create a private tunnel for ABUTRON, retaining the exact `tunnel_id`. Create a **restricted runtime API key** in [Platform API keys](https://platform.openai.com/settings/organization/api-keys) with only **Tunnels Read + Use**. Do not use admin permissions for runtime. Do not paste the key into ChatGPT, GitHub issues or shell command arguments. Make sure the tunnel belongs to the correct Platform organization and supported client/workspace, if relevant.

## One-time Ubuntu root operator command

In your production Ubuntu *root terminal*, after the approved scripts reach `abutron-ops/main`:

```bash
cd /root/abutron-ops
git fetch origin
git pull --ff-only origin main
bash -n ops/mcp_gateway/configure-private-tunnel-v1.sh
bash ops/mcp_gateway/configure-private-tunnel-v1.sh YOUR_REAL_TUNNEL_ID
```

The script prompts for the API key without echo; it runs `tunnel-client init` and `doctor --explain` as non-root `abutronmcp`, stores the key only in root-owned mode-0600 `/etc/abutron-mcp/tunnel.env`, and starts the non-root tunnel service only after the doctor check passes. No root-running Desktop Commander, public listener, MT5 EA, CRM/account switch or broker trade is enabled.

## Validation after activation (do not reveal the secret)

```bash
systemctl is-active abutron-mcp-tunnel.service
systemctl is-enabled abutron-mcp-tunnel.service
systemctl show abutron-mcp-tunnel.service -p User -p MainPID -p ActiveState -p SubState --no-pager
```

Expected `User=abutronmcp`, `ActiveState=active`. This proves a local daemon is running, **not** that a remote client or this ChatGPT Plus session has connected. For end-to-end proof, use a supported MCP client to initialize, list tools, execute a benign read-only operation, and verify it was routed through the tunnel. Examine `/healthz`, `/readyz` and `/health/mcp` locally as documented by the official [OpenAI tunnel-client guide](https://github.com/openai/tunnel-client/blob/master/docs/end-user-guide.md).

## Existing ChatGPT Plus limitation

Per [OpenAI custom MCP connection requirements](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt), custom full write-capable MCP connection creation is available to Business and Enterprise/Edu, **not ChatGPT Plus**. The private tunnel does not bypass this. Hosted Desktop Commander tool quotas are a separate service issue. Use GitHub's existing fixed, reviewed production workflows for ABUTRON tasks within Plus, rather than claiming the private MCP service has been attached.

## Recovery

If the tunnel is newly configured and needs stopping:

```bash
systemctl disable --now abutron-mcp-tunnel.service
```

This stops only the dedicated tunnel service; it does not change production trading. Revoke the runtime API key and tunnel association in Platform if retiring the connection. Do not print `/etc/abutron-mcp/tunnel.env` in logs.
