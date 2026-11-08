#!/usr/bin/env bash
# One-time local operator setup after creating a real OpenAI Platform Tunnel.
# Prompts for runtime key interactively. Never run through GitHub Actions.
# Uses the already staged nonroot abutronmcp service and its fixed MCP wrapper.
set -Eeuo pipefail
set +x
umask 077

if [[ "$(id -u)" != "0" || ! -t 0 ]]; then
  echo "ROOT_INTERACTIVE_UBUNTU_TERMINAL_REQUIRED" >&2
  exit 2
fi

TUNNEL_ID="${1:-}"
if [[ $# != 1 || ! "$TUNNEL_ID" =~ ^[A-Za-z0-9:_-]{10,180}$ ]]; then
  echo "Usage: bash ops/mcp_gateway/configure-private-tunnel-v1.sh YOUR_REAL_TUNNEL_ID" >&2
  exit 2
fi

TUNNEL=/usr/local/bin/tunnel-client
WRAPPER=/usr/local/libexec/abutron-dcmcp-agent-v1
ENVFILE=/etc/abutron-mcp/tunnel.env
STATE=/var/lib/abutron-mcp
UNIT=abutron-mcp-tunnel.service

[[ -x "$TUNNEL" && ! -L "$TUNNEL" && -x "$WRAPPER" && ! -L "$WRAPPER" ]] ||
  { echo "TUNNEL_OR_LOCAL_MCP_WRAPPER_NOT_STAGED" >&2; exit 2; }
[[ -d "$STATE" && ! -L "$STATE" && "$(stat -c '%U:%G' "$STATE")" == 'abutronmcp:abutronmcp' ]] ||
  { echo "PRIVATE_MCP_SERVICE_ACCOUNT_STATE_UNVERIFIED" >&2; exit 2; }
[[ "$(id -nG abutronmcp)" == 'abutronmcp' ]] ||
  { echo "MCP_SERVICE_ACCOUNT_GROUPS_UNEXPECTED" >&2; exit 2; }
[[ -f /etc/systemd/system/abutron-mcp-tunnel.service && ! -L /etc/systemd/system/abutron-mcp-tunnel.service ]] ||
  { echo "MCP_SYSTEMD_UNIT_NOT_STAGED" >&2; exit 2; }
[[ ! -e "$ENVFILE" && ! -L "$ENVFILE" ]] ||
  { echo "REFUSE_OVERWRITE_EXISTING_TUNNEL_KEY_RUN_STATUS_INSTEAD" >&2; exit 2; }
! systemctl is-active --quiet "$UNIT" ||
  { echo "TUNNEL_ALREADY_RUNNING_REFUSE_RECONFIGURE" >&2; exit 2; }

echo "OpenAI Platform tunnel ID accepted. Runtime API key must have Tunnels Read + Use only."
printf "Enter restricted tunnel runtime API key (input hidden): " >&2
IFS= read -rs API_KEY
echo >&2
if [[ ! "$API_KEY" =~ ^[A-Za-z0-9._-]{24,512}$ ]]; then
  unset API_KEY
  echo "KEY_FORMAT_INVALID_OR_EMPTY" >&2
  exit 2
fi

# No key passed on the command line, committed to GitHub, or printed.
config_env=(HOME="$STATE" XDG_CONFIG_HOME="$STATE/.config" CONTROL_PLANE_API_KEY="$API_KEY")
echo "Initializing private stdio tunnel profile as non-root abutronmcp..."
runuser -u abutronmcp -- /usr/bin/env "${config_env[@]}" \
  "$TUNNEL" init \
  --sample sample_mcp_stdio_local \
  --profile abutron-production \
  --tunnel-id "$TUNNEL_ID" \
  --mcp-command "$WRAPPER"

echo "Verifying tunnel and local MCP configuration..."
runuser -u abutronmcp -- /usr/bin/env "${config_env[@]}" \
  "$TUNNEL" doctor --profile abutron-production --explain ||
  { unset API_KEY; echo "TUNNEL_DOCTOR_FAILED_NOT_ACTIVATED" >&2; exit 1; }

TMP="$(mktemp /etc/abutron-mcp/.runtime-env.XXXXXXXX)"
trap 'rm -f -- "$TMP"' EXIT
printf 'CONTROL_PLANE_API_KEY=%s\n' "$API_KEY" > "$TMP"
chown root:root "$TMP"
chmod 0600 "$TMP"
unset API_KEY
mv -T -- "$TMP" "$ENVFILE"
trap - EXIT
systemctl enable --now "$UNIT"
systemctl is-active --quiet "$UNIT" ||
  { echo "TUNNEL_SERVICE_NOT_ACTIVE_INSPECT_JOURNAL" >&2; exit 1; }
echo "PRIVATE_MCP_TUNNEL_SYSTEMD_ACTIVE=YES"
echo "LOCAL_BROWSER_CHATGPT_PLUS_CUSTOM_MCP_NOT_PROVEN"
echo "CHECK_READINESS_WITH=systemctl_status_and_tunnel_health"
