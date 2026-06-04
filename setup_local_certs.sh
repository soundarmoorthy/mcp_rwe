#!/usr/bin/env bash
# =============================================================================
# setup_local_certs.sh
# Generates locally-trusted TLS certificates so the RWE MCP server can run
# over HTTPS on your local machine.
#
# Strategy (macOS):
#   1. If `mkcert` is available (or can be installed via Homebrew) → use it.
#      mkcert creates certificates that are automatically trusted by your OS
#      Keychain and by browsers (no "Not Secure" warnings).
#   2. Fallback → openssl self-signed certificate (manual trust required).
#
# After running this script, start the server with HTTPS:
#   SSL_CERTFILE=certs/localhost.pem SSL_KEYFILE=certs/localhost-key.pem python server.py
# Or use the generated run_https.sh helper.
# =============================================================================

set -euo pipefail

CERTS_DIR="$(cd "$(dirname "$0")" && pwd)/certs"
DOMAIN="localhost"
CERT_FILE="$CERTS_DIR/$DOMAIN.pem"
KEY_FILE="$CERTS_DIR/$DOMAIN-key.pem"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}   Local HTTPS Certificate Setup – RWE MCP Server          ${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# --------------------------------------------------------------------------
# Create certs directory
# --------------------------------------------------------------------------
mkdir -p "$CERTS_DIR"
echo -e "${GREEN}✔ Certificate directory: $CERTS_DIR${NC}"

# --------------------------------------------------------------------------
# Detect or install mkcert
# --------------------------------------------------------------------------
use_mkcert=false

if command -v mkcert &>/dev/null; then
    echo -e "${GREEN}✔ mkcert found: $(command -v mkcert)${NC}"
    use_mkcert=true
elif command -v brew &>/dev/null; then
    echo -e "${YELLOW}⚠ mkcert not found – installing via Homebrew …${NC}"
    brew install mkcert nss 2>&1 | tail -5
    use_mkcert=true
else
    echo -e "${YELLOW}⚠ mkcert not found and Homebrew is unavailable.${NC}"
    echo -e "${YELLOW}  Falling back to openssl (self-signed, manual trust needed).${NC}"
fi

# --------------------------------------------------------------------------
# Generate certificates
# --------------------------------------------------------------------------
if $use_mkcert; then
    echo ""
    echo -e "${CYAN}► Installing mkcert root CA into the system trust store …${NC}"
    mkcert -install

    echo ""
    echo -e "${CYAN}► Generating certificate for: $DOMAIN 127.0.0.1 ::1${NC}"
    # Output filenames matching our expected paths
    mkcert \
        -cert-file "$CERT_FILE" \
        -key-file  "$KEY_FILE" \
        "$DOMAIN" "127.0.0.1" "::1"

    echo ""
    echo -e "${GREEN}✔ Trusted certificate generated (no browser warnings).${NC}"

else
    # --------------------------------------------------------------------------
    # openssl fallback – self-signed certificate
    # --------------------------------------------------------------------------
    echo ""
    echo -e "${CYAN}► Generating self-signed certificate via openssl …${NC}"

    openssl req -x509 -nodes \
        -newkey rsa:2048 \
        -days 825 \
        -keyout "$KEY_FILE" \
        -out    "$CERT_FILE" \
        -subj   "/CN=localhost/O=RWE-MCP-Dev/C=US" \
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1" \
        2>&1

    echo ""
    echo -e "${GREEN}✔ Self-signed certificate generated.${NC}"
    echo ""
    echo -e "${YELLOW}⚠  MANUAL TRUST REQUIRED (self-signed cert):${NC}"
    echo -e "${YELLOW}   macOS Keychain:${NC}"
    echo -e "     sudo security add-trusted-cert -d -r trustRoot \\"
    echo -e "          -k /Library/Keychains/System.keychain \"$CERT_FILE\""
    echo -e ""
    echo -e "${YELLOW}   Or open Keychain Access, import the cert, and set it to 'Always Trust'.${NC}"
fi

# --------------------------------------------------------------------------
# Verify files exist
# --------------------------------------------------------------------------
echo ""
if [[ -f "$CERT_FILE" && -f "$KEY_FILE" ]]; then
    echo -e "${GREEN}✔ Certificate : $CERT_FILE${NC}"
    echo -e "${GREEN}✔ Private key : $KEY_FILE${NC}"

    # Print cert info
    echo ""
    echo -e "${CYAN}Certificate details:${NC}"
    openssl x509 -in "$CERT_FILE" -noout \
        -subject -issuer \
        -dates   \
        -ext subjectAltName 2>/dev/null || true
else
    echo -e "${RED}✘ Certificate generation failed. Check output above.${NC}"
    exit 1
fi

# --------------------------------------------------------------------------
# Write / overwrite run_https.sh helper
# --------------------------------------------------------------------------
RUN_SCRIPT="$(dirname "$CERT_FILE")/../run_https.sh"
RUN_SCRIPT="$(cd "$(dirname "$0")" && pwd)/run_https.sh"

cat > "$RUN_SCRIPT" <<'RUNSCRIPT'
#!/usr/bin/env bash
# Auto-generated by setup_local_certs.sh
# Starts the RWE MCP server with HTTPS enabled.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export SSL_CERTFILE="$SCRIPT_DIR/certs/localhost.pem"
export SSL_KEYFILE="$SCRIPT_DIR/certs/localhost-key.pem"
export MCP_HOST="${MCP_HOST:-127.0.0.1}"
export MCP_PORT="${MCP_PORT:-9090}"

echo "Starting RWE MCP Server with HTTPS …"
echo "  Endpoint : https://$MCP_HOST:$MCP_PORT/mcp"
echo "  Cert     : $SSL_CERTFILE"
echo ""

cd "$SCRIPT_DIR"
python server.py
RUNSCRIPT

chmod +x "$RUN_SCRIPT"
echo ""
echo -e "${GREEN}✔ Helper script created: $RUN_SCRIPT${NC}"

# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  All done! Start the server with HTTPS using either:${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "  ${GREEN}./run_https.sh${NC}"
echo ""
echo -e "  or manually:"
echo -e "  ${GREEN}SSL_CERTFILE=certs/localhost.pem SSL_KEYFILE=certs/localhost-key.pem python server.py${NC}"
echo ""
echo -e "  MCP endpoint will be available at:"
echo -e "  ${CYAN}https://localhost:9090/mcp${NC}"
echo ""
