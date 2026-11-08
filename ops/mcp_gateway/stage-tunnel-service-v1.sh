#!/usr/bin/env bash
# Stage a private outbound MCP tunnel service. Never runs as root.
# Root operator workflow only. No secrets, MT5, CRM, trading, or tunnel start.
set -Eeuo pipefail
umask 077

if [[ "$(id -u)" != "0" ]]; then
  echo 'ROOT_OPERATOR_REQUIRED' >&2
  exit 1
fi

action="${1:-}"
NODE=/opt/abutron-mcp/node/bin/node
PKG=/opt/abutron-dcmcp/node_modules/@wonderwhy-er/desktop-commander/dist/index.js
TUNNEL=/usr/local/bin/tunnel-client
WRAPPER=/usr/local/libexec/abutron-dcmcp-agent-v1
UNIT=/etc/systemd/system/abutron-mcp-tunnel.service
STATE=/var/lib/abutron-mcp
CONFIG=/etc/abutron-mcp

preflight() {
  for p in "$NODE" "$PKG" "$TUNNEL"; do
    [[ -f "$p" && ! -L "$p" ]] || { echo "MISSING_OR_SYMLINK_DEPENDENCY=$p" >&2; exit 2; }
    [[ "$(stat -c '%u' "$p")" == '0' ]] ||
      { echo "DEPENDENCY_NOT_ROOT_OWNED=$p" >&2; exit 2; }
  done
  [[ -x "$NODE" && -x "$TUNNEL" ]] || { echo 'NODE_OR_TUNNEL_NOT_EXECUTABLE' >&2; exit 2; }
  [[ "$("$NODE" --version)" == 'v22.23.4' ]] ||
    { echo 'UNEXPECTED_ISOLATED_NODE_VERSION' >&2; exit 2; }
  "$TUNNEL" help quickstart >/dev/null ||
    { echo 'OFFICIAL_TUNNEL_CLIENT_CANNOT_START' >&2; exit 2; }
  echo 'MCP_GATEWAY_PREREQUISITES_PASS'
}

case "$action" in
  preflight)
    preflight
    ;;
  stage)
    preflight
    [[ ! -e "$UNIT" && ! -L "$UNIT" ]] || {
      echo 'REFUSE_OVERWRITE_EXISTING_MCP_UNIT' >&2
      exit 2
    }
    [[ ! -e "$WRAPPER" && ! -L "$WRAPPER" ]] || {
      echo 'REFUSE_OVERWRITE_EXISTING_MCP_WRAPPER' >&2
      exit 2
    }
    if ! getent passwd abutronmcp >/dev/null; then
      /usr/sbin/useradd --system --user-group --home-dir "$STATE" \
        --shell /usr/sbin/nologin --no-create-home abutronmcp
    fi
    [[ "$(id -un "$(id -u abutronmcp)")" == 'abutronmcp' ]] ||
      { echo 'SERVICE_ACCOUNT_UNVERIFIED' >&2; exit 2; }
    [[ "$(id -nG abutronmcp)" == 'abutronmcp' ]] ||
      { echo 'SERVICE_ACCOUNT_HAS_UNEXPECTED_GROUPS' >&2; exit 2; }
    [[ -d "$STATE" || ! -e "$STATE" ]] &&
      [[ ! -L "$STATE" ]] || { echo 'UNSAFE_STATE_DIRECTORY' >&2; exit 2; }
    install -d -o abutronmcp -g abutronmcp -m 0700 "$STATE"
    install -d -o root -g root -m 0700 "$CONFIG"
    install -d -o root -g root -m 0755 /usr/local/libexec
    printf '#!/bin/sh\nexec "%s" "%s" --no-onboarding\n' \
      "$NODE" "$PKG" > "$WRAPPER"
    chown root:root "$WRAPPER"
    chmod 0755 "$WRAPPER"
    cat > "$UNIT" <<'SERVICE'
[Unit]
Description=ABUTRON Private Non-Root MCP Outbound Tunnel
After=network-online.target
Wants=network-online.target
ConditionPathExists=/etc/abutron-mcp/tunnel.env

[Service]
Type=simple
User=abutronmcp
Group=abutronmcp
WorkingDirectory=/var/lib/abutron-mcp
Environment=HOME=/var/lib/abutron-mcp
Environment=XDG_CONFIG_HOME=/var/lib/abutron-mcp/.config
EnvironmentFile=/etc/abutron-mcp/tunnel.env
ExecStart=/usr/local/bin/tunnel-client run --profile abutron-production
Restart=on-failure
RestartSec=10
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/abutron-mcp
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectKernelLogs=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
CapabilityBoundingSet=
AmbientCapabilities=
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
SERVICE
    chown root:root "$UNIT"
    chmod 0644 "$UNIT"
    systemctl daemon-reload
    runuser -u abutronmcp -- "$NODE" --version |
      grep -Fx 'v22.23.4' >/dev/null
    runuser -u abutronmcp -- /usr/bin/test -r "$PKG"
    [[ ! -e "$CONFIG/tunnel.env" ]] ||
      { echo 'UNEXPECTED_EXISTING_TUNNEL_CREDENTIAL_FILE' >&2; exit 2; }
    ! systemctl is-enabled --quiet abutron-mcp-tunnel.service ||
      { echo 'UNEXPECTED_TUNNEL_ENABLED' >&2; exit 2; }
    ! systemctl is-active --quiet abutron-mcp-tunnel.service ||
      { echo 'UNEXPECTED_TUNNEL_ACTIVE' >&2; exit 2; }
    echo 'NONROOT_MCP_SERVICE_STAGED_INACTIVE=YES'
    echo 'SERVICE_USER=abutronmcp'
    echo 'TUNNEL_ID_AND_RUNTIME_KEY=NOT_CONFIGURED'
    echo 'NO_PRODUCTION_TRADING_SERVICE_CHANGED'
    ;;
  status)
    preflight
    id abutronmcp
    systemctl is-enabled abutron-mcp-tunnel.service || true
    systemctl is-active abutron-mcp-tunnel.service || true
    ;;
  rollback)
    # Only stage artifacts owned by this script. Keep credentials and
    # account data for deliberate revocation; never remove broker files.
    systemctl disable --now abutron-mcp-tunnel.service || true
    [[ ! -f "$UNIT" || -L "$UNIT" ]] ||
      rm -- "$UNIT"
    [[ ! -f "$WRAPPER" || -L "$WRAPPER" ]] ||
      rm -- "$WRAPPER"
    systemctl daemon-reload
    echo 'MCP_SERVICE_UNIT_AND_WRAPPER_REMOVED_CREDENTIALS_NOT_DELETED'
    ;;
  *)
    echo 'Usage: stage-tunnel-service-v1.sh {preflight|stage|status|rollback}' >&2
    exit 2
    ;;
esac
