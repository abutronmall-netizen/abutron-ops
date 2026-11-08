# ABUTRON Desktop Commander — Plus-compatible local readiness

**Verified on Ubuntu production `localhost`, 2026-11-08 12:59 UTC:** local Desktop Commander package **0.3.1** exists at `/opt/abutron-dcmcp/node_modules/@wonderwhy-er/desktop-commander/dist/index.js`; the package requires Node **>=22.12**; global Node is **v18.19.1**; isolated Node and official OpenAI tunnel-client are missing; no tunnel systemd unit is installed. Source: [read-only host run 42482747221](https://github.com/abutronmall-netizen/abutron-ops/actions/runs/42482747221).

## Install the missing Node runtime (one root-console command)

A one-time operator command on the **Ubuntu production root terminal** is necessary because `abutrongha` is authorized for fixed staging/rollback only. Do not run unreviewed GitHub code as root.

```bash
cd /root/abutron-ops
git fetch origin
git pull --ff-only origin main
bash -n ops/mcp_gateway/install-isolated-node-v1.sh
bash ops/mcp_gateway/install-isolated-node-v1.sh
/opt/abutron-mcp/node/bin/node --version
/usr/bin/node --version
```

This installs **official Node.js v22.23.4** only under `/opt/abutron-mcp/node`, with pinned upstream SHA256 `1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce`. It does not replace global Node, install packages, connect a tunnel, start a service, modify MT5/CRM, or enable trading. Archive source: [Node.js 22.23.4 security release](https://nodejs.org/en/blog/release/v22.23.4).

After the root command, GitHub owner creates an issue titled exactly `ABUTRON OPS SMOKE DESKTOP COMMANDER V1`. The fixed owner-only workflow `.github/workflows/abutron-dcmcp-local-smoke-v1.yml` launches the local MCP child under the unprivileged runner with temporary HOME, tests MCP initialize and tools/list, then exits. **It never invokes any Desktop Commander tool or broker action.** A PASS validates only local MCP availability, not a ChatGPT browser connection.

## ChatGPT Plus restriction

The connected **Remote Desktop Commander** host relay remains a separate integration; its monthly tool quota is exhausted, and a locally installed server cannot reset it.

Official ChatGPT guidance at [Connecting custom MCP servers](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt) currently limits **full custom MCP read/write creation** to Business and Enterprise/Edu workspaces; it is not an available direct writable connection on Plus. Therefore the OpenAI Secure MCP Tunnel under draft [PR #47](https://github.com/abutronmall-netizen/abutron-ops/pull/47) **must not be advertised as restoring Desktop Commander tools inside this Plus chat**. Installing the tunnel-client is optional for other authorized supported surfaces, but does not fix the Plus limitation.

**Best current Plus path for production changes:** the owner-gated GitHub Actions runner with fixed reviewed operations. Extend it to narrow MT5 deployment functionality only after proper account/backup/operator controls, not broad shell access.

## Verified completion definition

1. `ISOLATED_NODE_INSTALL_PASS=v22.23.4` from actual Ubuntu command.
2. A successful fixed [local MCP smoke workflow](https://github.com/abutronmall-netizen/abutron-ops/actions) reports `MCP_INIT=PASS` and `MCP_TOOLS_LIST=PASS`.
3. If a supported MCP client is used later, real authenticated tool discovery and a benign read-only operation complete end to end. Until that point, **ChatGPT Plus direct Desktop Commander access remains unverified and unavailable**.

No production system changes were performed merely by merging these scripts.
