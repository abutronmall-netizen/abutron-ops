#!/usr/bin/env bash
# Install pinned Node.js ONLY under /opt/abutron-mcp/node for local
# Desktop Commander. Does not touch /usr/bin/node, global npm, MT5 or systemd.
set -Eeuo pipefail
umask 077

if [[ "$(id -u)" != "0" ]]; then
  echo "ROOT_OPERATOR_REQUIRED: run this reviewed installer from the Ubuntu root terminal" >&2
  exit 1
fi
if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "UNSUPPORTED_OS_OR_ARCH: expected Ubuntu Linux x86_64" >&2
  exit 1
fi

VERSION=v22.23.4
FILENAME=node-v22.23.4-linux-x64.tar.xz
SHA256=1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce
URL="https://nodejs.org/dist/${VERSION}/${FILENAME}"
ROOT=/opt/abutron-mcp
DEST="${ROOT}/node"

for bin in curl tar sha256sum mktemp mv install; do
  command -v "$bin" >/dev/null || { echo "MISSING_REQUIRED_COMMAND=$bin" >&2; exit 1; }
done
if [[ -L "$ROOT" || -L "$DEST" ]]; then
  echo "REFUSE_SYMLINK_AT_DESTINATION" >&2
  exit 1
fi
if [[ -e "$DEST" ]]; then
  if [[ -f "$DEST/bin/node" && ! -L "$DEST/bin/node" &&
        "$("$DEST/bin/node" --version)" == "$VERSION" ]]; then
    # The official tar permissions can be masked by root umask 077.
    # Restore read/execute access ONLY to the isolated Node binary path.
    test "$(stat -c '%u:%g' "$DEST/bin")" = '0:0'
    test "$(stat -c '%u:%g' "$DEST/bin/node")" = '0:0'
    [[ ! -L "$DEST/bin" && ! -L "$DEST/bin/node" ]]
    chmod 0755 "$DEST/bin" "$DEST/bin/node"
    echo "ISOLATED_NODE_ALREADY_INSTALLED=$VERSION"
    echo "ISOLATED_NODE_NONROOT_EXECUTION_READY=YES"
    exit 0
  fi
  echo "REFUSE_OVERWRITE_EXISTING_NODE_RUNTIME: review manually" >&2
  exit 1
fi

if [[ -e "$ROOT" ]]; then
  [[ -d "$ROOT" && ! -L "$ROOT" ]] || { echo "ROOT_PATH_NOT_DIRECTORY" >&2; exit 1; }
  [[ "$(stat -c '%u' "$ROOT")" == 0 ]] || { echo "ROOT_PATH_NOT_ROOT_OWNED" >&2; exit 1; }
  [[ "$(stat -c '%a' "$ROOT")" =~ ^(700|750|755)$ ]] ||
    { echo "ROOT_PATH_PERMISSIONS_UNEXPECTED" >&2; exit 1; }
else
  install -d -o root -g root -m 0755 "$ROOT"
fi

temp="$(mktemp -d "${ROOT}/.node-download.XXXXXXXX")"
trap 'rm -rf -- "$temp"' EXIT
echo "DOWNLOADING_OFFICIAL_NODE=$VERSION"
curl --proto '=https' --tlsv1.2 --fail --silent --show-error --location \
  --connect-timeout 15 --max-time 180 --output "${temp}/${FILENAME}" "$URL"
printf '%s  %s\n' "$SHA256" "${temp}/${FILENAME}" | sha256sum --check --status ||
  { echo "NODE_ARCHIVE_SHA256_MISMATCH" >&2; exit 1; }
echo "OFFICIAL_NODE_ARCHIVE_SHA256_VERIFIED"

install -d -o root -g root -m 0755 "${temp}/runtime"
tar -xJf "${temp}/${FILENAME}" -C "${temp}/runtime" --strip-components=1 \
  --no-same-owner --no-same-permissions
[[ -x "${temp}/runtime/bin/node" && ! -L "${temp}/runtime/bin/node" ]] ||
  { echo "UNSAFE_NODE_BINARY" >&2; exit 1; }
[[ "$("${temp}/runtime/bin/node" --version)" == "$VERSION" ]] ||
  { echo "NODE_VERSION_MISMATCH" >&2; exit 1; }

chown -R root:root "${temp}/runtime"
chmod -R go-w "${temp}/runtime"
chmod -R go+rX "${temp}/runtime"
[[ ! -e "$DEST" && ! -L "$DEST" ]] || { echo "DESTINATION_APPEARED_DURING_INSTALL" >&2; exit 1; }
mv -T -- "${temp}/runtime" "$DEST"
echo "ISOLATED_NODE_INSTALL_PASS=$("$DEST/bin/node" --version)"
echo "GLOBAL_NODE_LEFT_UNCHANGED=$(/usr/bin/node --version 2>/dev/null || echo unavailable)"
echo "NO_TUNNEL_OR_MCP_SERVICE_STARTED"
