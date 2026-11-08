#!/usr/bin/env bash
# ABUTRON Secure MCP Tunnel deployment: root operator only, never GitHub runner.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == "0" ]] || { echo 'Root shell required' >&2; exit 1; }
action="$1"
case "$action" in preflight|stage|configure|doctor|enable|rollback) ;; *) echo "Usage: $0 {preflight|stage|configure TUNNEL_ID|doctor|enable|rollback}" >&2; exit 2;; esac
NODE=/opt/abutron-mcp/node/bin/node
PKG=/opt/abutron-dcmcp/node_modules/@wonderwhy-er/desktop-commander/dist/index.js
TUNNEL=/usr/local/bin/tunnel-client
WRAPPER=/usr/local/sbin/abutron-dcmcp-isolated
UNIT=/etc/systemd/system/abutron-mcp-tunnel.service
ENVFILE=/etc/abutron-mcp/tunnel.env
preflight() {
  for p in "$NODE" "$TUNNEL"; do
    [[ -f "$p" && -x "$p" && ! -L "$p" ]] || { echo "Missing or unsafe executable: $p" >&2; return 1; }
    [[ "$(stat -c %u "$p")" == 0 ]] || { echo "Not root-owned: $p" >&2; return 1; }
  done
  [[ -f "$PKG" && ! -L "$PKG" ]] || { echo 'Desktop Commander local package missing' >&2; return 1; }
  "$NODE" -e 'const v=process.versions.node.split(".").map(Number);if(v[0]<22||(v[0]===22&&v[1]<12))process.exit(1)' ||
    { echo 'Requires isolated Node >=22.12; do NOT replace production /usr/bin/node' >&2; return 1; }
  "$TUNNEL" help quickstart >/dev/null
  echo "PREFLIGHT_PASS: no production services modified"
}
diagnose() {
  [[ -f "$ENVFILE" && "$(stat -c %a "$ENVFILE")" == 600 && "$(stat -c %u "$ENVFILE")" == 0 ]] ||
    { echo 'Missing root-owned mode-0600 tunnel credentials' >&2; return 1; }
  set -a
  source "$ENVFILE"
  set +a
  "$TUNNEL" doctor --profile abutron-production --explain
}
case "$action" in
  preflight) preflight;;
  stage)
    preflight
    [[ ! -e "$UNIT" && ! -L "$UNIT" && ! -e "$WRAPPER" && ! -L "$WRAPPER" ]] ||
      { echo 'Refusing to overwrite existing service or launcher' >&2; exit 1; }
    install -d -o root -g root -m 0700 /etc/abutron-mcp
    printf '#!/bin/sh\nexec "%s" "%s" --no-onboarding\n' "$NODE" "$PKG" > "$WRAPPER"
    chown root:root "$WRAPPER"; chmod 0700 "$WRAPPER"
    cat > "$UNIT" <<'SYSTEMD'
[Unit]
Description=ABUTRON outbound private MCP tunnel
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root
Environment=HOME=/root
EnvironmentFile=/etc/abutron-mcp/tunnel.env
ExecStart=/usr/local/bin/tunnel-client run --profile abutron-production
Restart=on-failure
RestartSec=10
UMask=0077
[Install]
WantedBy=multi-user.target
SYSTEMD
    chown root:root "$UNIT"; chmod 0644 "$UNIT"
    systemctl daemon-reload
    echo 'STAGED_ONLY: service not started or enabled';;
  configure)
    [[ "$#" == 2 && "$2" =~ ^tunnel_[A-Za-z0-9_-]+$ ]] || { echo 'Supply a real tunnel_ID' >&2; exit 2; }
    [[ -x "$WRAPPER" && -f "$UNIT" && ! -e "$ENVFILE" ]] || { echo 'Stage first; refusing credential overwrite' >&2; exit 1; }
    printf 'Paste scoped tunnel runtime API key (hidden): ' >&2
    IFS= read -rs api_key; echo >&2
    [[ "$api_key" =~ ^[A-Za-z0-9._-]+$ ]] || { echo 'Invalid API key characters' >&2; exit 1; }
    printf 'CONTROL_PLANE_API_KEY=%s\n' "$api_key" > "$ENVFILE"
    chmod 0600 "$ENVFILE"; chown root:root "$ENVFILE"
    CONTROL_PLANE_API_KEY="$api_key" "$TUNNEL" init --sample sample_mcp_stdio_local \
      --profile abutron-production --tunnel-id "$2" --mcp-command "$WRAPPER"
    unset api_key
    echo 'Profile configured; run doctor, then enable';;
  doctor) diagnose;;
  enable)
    diagnose
    systemctl enable --now abutron-mcp-tunnel.service
    systemctl is-active --quiet abutron-mcp-tunnel.service
    echo 'TUNNEL_SERVICE_ACTIVE: browser tool access NOT yet proven';;
  rollback)
    systemctl disable --now abutron-mcp-tunnel.service || true
    [[ ! -f "$UNIT" ]] || rm -- "$UNIT"
    [[ ! -f "$WRAPPER" ]] || rm -- "$WRAPPER"
    systemctl daemon-reload
    echo 'Tunnel unit/wrapper removed. Runtime key/profile intentionally retained for reviewed revocation.';;
esac
