#!/bin/bash
#
# entrypoint.sh for the warp-instance container
# This script automates the setup of warp-cli based on official documentation.
#

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration via Environment Variables (with defaults) ---
# WARP_MODE: The operational mode. 'proxy' is for this project's goal.
# Others: 'warp', 'doh', 'warp+doh'.
WARP_MODE="${WARP_MODE:-proxy}"

# WARP_TUNNEL_PROTOCOL: The tunnel protocol to use. MASQUE is the default.
# Options: 'MASQUE', 'WireGuard'. Case-sensitive.
WARP_TUNNEL_PROTOCOL="${WARP_TUNNEL_PROTOCOL:-MASQUE}"

# WARP_FAMILIES_MODE: Optional. Configures 1.1.1.1 for Families.
# Options: 'off', 'malware', 'full'.
# If the variable is not set, this setting will be skipped.
# WARP_FAMILIES_MODE="${WARP_FAMILIES_MODE}" 

# PROXY_PORT: The SOCKS5 proxy port, only used if WARP_MODE is 'proxy'.
PROXY_PORT="${PROXY_PORT:-40000}"

echo "--- WARP Container Entrypoint ---"
echo "Mode: ${WARP_MODE}"
echo "Tunnel Protocol: ${WARP_TUNNEL_PROTOCOL}"
[ -n "$WARP_FAMILIES_MODE" ] && echo "Families Mode: ${WARP_FAMILIES_MODE}"
[ "${WARP_MODE}" = "proxy" ] && echo "Proxy Port: ${PROXY_PORT}"
echo "---------------------------------"

# 1. Registration
# Check if already registered. If not, register a new account.
if [ ! -f "/var/lib/cloudflare-warp/reg.json" ]; then
    echo ">>> WARP is not registered. Performing new registration..."
    warp-cli registration new
else
    echo ">>> WARP is already registered. Skipping registration."
fi

# 2. Set License Key (Optional)
# If a WARP+ license key is provided, apply it.
if [ -n "$WARP_LICENSE_KEY" ]; then
    echo ">>> Setting WARP+ license key..."
    warp-cli registration license "$WARP_LICENSE_KEY"
fi

# 3. Configure Tunnel Protocol (Official Method)
echo ">>> Setting tunnel protocol to ${WARP_TUNNEL_PROTOCOL}..."
warp-cli tunnel protocol set "${WARP_TUNNEL_PROTOCOL}"

# 4. Configure Families DNS (Optional)
if [ -n "$WARP_FAMILIES_MODE" ]; then
    echo ">>> Setting 1.1.1.1 for Families mode to ${WARP_FAMILIES_MODE}..."
    warp-cli dns families "${WARP_FAMILIES_MODE}"
fi

# 5. Set Operational Mode and Proxy Port
echo ">>> Setting WARP mode to ${WARP_MODE}..."
warp-cli set-mode "${WARP_MODE}"

if [ "${WARP_MODE}" = "proxy" ]; then
    echo ">>> Setting proxy port to ${PROXY_PORT}..."
    warp-cli set-proxy-port "${PROXY_PORT}"
fi

# 6. Start the service and keep the container alive
echo ">>> Starting warp-svc..."
systemctl start warp-svc
echo "--- WARP service started. Container is up and running. ---"
echo "The controller application will now manage the connection state."

# Keep the container running.
tail -f /dev/null