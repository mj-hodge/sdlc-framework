#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# dns-register-app.sh
# Registers a new app's DNS subdomain in Azure DNS for gorillacommerce.ai
# ---------------------------------------------------------------------------

SCRIPT_NAME="$(basename "$0")"

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME --app-name <slug> --target <fqdn> [OPTIONS]

Registers a CNAME record in Azure DNS for the gorillacommerce.ai zone.

REQUIRED ARGUMENTS:
  --app-name <slug>     App slug, e.g. "myapp"
  --target <fqdn>       Azure Container Apps FQDN, e.g.
                        "ca-mcp-myapp.eastus.azurecontainerapps.io"

OPTIONAL ARGUMENTS:
  --env <env>           "prod" or "dev" (default: prod)
                          prod → myapp.gorillacommerce.ai
                          dev  → myapp.dev.gorillacommerce.ai
  --zone <zone>         DNS zone name (default: gorillacommerce.ai)
  --resource-group <rg> Azure resource group containing the DNS zone
                        (default: rg-dns-gorillacommerce)
  --ttl <seconds>       TTL for the record in seconds (default: 3600)
  --both                Create BOTH prod and dev records in one run
  --help                Show this help message and exit

EXAMPLES:
  # Register prod record
  $SCRIPT_NAME --app-name myapp --target ca-mcp-myapp.eastus.azurecontainerapps.io

  # Register dev record only
  $SCRIPT_NAME --app-name myapp --target ca-mcp-myapp-dev.eastus.azurecontainerapps.io --env dev

  # Register both prod and dev records
  $SCRIPT_NAME --app-name myapp --target ca-mcp-myapp.eastus.azurecontainerapps.io --both
EOF
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log()  { printf '[INFO]  %s\n' "$*"; }
warn() { printf '[WARN]  %s\n' "$*" >&2; }
die()  { printf '[ERROR] %s\n' "$*" >&2; exit 1; }

check_az_cli() {
  if ! command -v az &>/dev/null; then
    die "Azure CLI (az) is not installed or not in PATH."
  fi

  # Check if logged in by attempting to get the signed-in user
  if ! az account show &>/dev/null; then
    die "Not logged in to Azure CLI. Run 'az login' first."
  fi

  log "Azure CLI authenticated as: $(az account show --query 'user.name' -o tsv)"
}

# Derive the DNS record name from app name and environment
record_name_for_env() {
  local app_name="$1"
  local env="$2"

  case "$env" in
    prod) printf '%s' "$app_name" ;;
    dev)  printf '%s.dev' "$app_name" ;;
    *)    die "Unknown env '${env}'. Must be 'prod' or 'dev'." ;;
  esac
}

# Create or update a CNAME record, then verify and print the resulting URL
register_record() {
  local record_name="$1"
  local target="$2"
  local zone="$3"
  local resource_group="$4"
  local ttl="$5"

  local fqdn="${record_name}.${zone}"

  log "Registering CNAME: ${fqdn} → ${target}"
  log "  Zone:           ${zone}"
  log "  Resource group: ${resource_group}"
  log "  TTL:            ${ttl}s"

  # Create or update the CNAME record set
  az network dns record-set cname set-record \
    --resource-group "$resource_group" \
    --zone-name      "$zone" \
    --record-set-name "$record_name" \
    --cname          "$target" \
    --ttl            "$ttl" \
    --output table

  log "Record created/updated. Verifying..."

  # Verify the record was created successfully
  local result
  result="$(az network dns record-set cname show \
    --resource-group  "$resource_group" \
    --zone-name       "$zone" \
    --name            "$record_name" \
    --query '{name:name,fqdn:fqdn,cname:CNAMERecord.cname,ttl:TTL}' \
    --output json)"

  local verified_cname
  verified_cname="$(printf '%s' "$result" | az rest --method post \
    --url /dev/stdin 2>/dev/null || true)"

  # Use a simple grep/python fallback for JSON parsing without jq dependency
  if command -v python3 &>/dev/null; then
    verified_cname="$(printf '%s' "$result" | python3 -c \
      "import sys,json; d=json.load(sys.stdin); print(d.get('cname','(unknown)'))")"
  else
    verified_cname="$(printf '%s' "$result" | grep -oP '(?<="cname": ")[^"]*' || echo '(unknown)')"
  fi

  log "Verification successful."
  log "  Record name:  ${record_name}"
  log "  CNAME target: ${verified_cname}"
  printf '\n'
  printf '  URL: https://%s\n' "$fqdn"
  printf '\n'
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

APP_NAME=""
TARGET=""
ENV="prod"
ZONE="gorillacommerce.ai"
RESOURCE_GROUP="rg-dns-gorillacommerce"
TTL=3600
BOTH=false

if [[ $# -eq 0 ]]; then
  usage
  exit 0
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-name)
      APP_NAME="${2:-}"
      [[ -z "$APP_NAME" ]] && die "--app-name requires a value"
      shift 2
      ;;
    --target)
      TARGET="${2:-}"
      [[ -z "$TARGET" ]] && die "--target requires a value"
      shift 2
      ;;
    --env)
      ENV="${2:-}"
      [[ -z "$ENV" ]] && die "--env requires a value"
      shift 2
      ;;
    --zone)
      ZONE="${2:-}"
      [[ -z "$ZONE" ]] && die "--zone requires a value"
      shift 2
      ;;
    --resource-group)
      RESOURCE_GROUP="${2:-}"
      [[ -z "$RESOURCE_GROUP" ]] && die "--resource-group requires a value"
      shift 2
      ;;
    --ttl)
      TTL="${2:-}"
      [[ -z "$TTL" ]] && die "--ttl requires a value"
      [[ "$TTL" =~ ^[0-9]+$ ]] || die "--ttl must be a positive integer"
      shift 2
      ;;
    --both)
      BOTH=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "Unknown argument: $1. Run '$SCRIPT_NAME --help' for usage."
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

[[ -z "$APP_NAME" ]] && die "--app-name is required"
[[ -z "$TARGET" ]]   && die "--target is required"

# Validate env (only if --both is not set, where we override it ourselves)
if [[ "$BOTH" == false ]]; then
  case "$ENV" in
    prod|dev) ;;
    *) die "--env must be 'prod' or 'dev', got: '${ENV}'" ;;
  esac
fi

# Validate app-name is a safe DNS label (alphanumeric + hyphens, no leading/trailing hyphen)
if [[ ! "$APP_NAME" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$ ]] && [[ ! "$APP_NAME" =~ ^[a-zA-Z0-9]$ ]]; then
  die "--app-name '${APP_NAME}' is not a valid DNS label (use alphanumeric and hyphens only, no leading/trailing hyphens)"
fi

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

check_az_cli

if [[ "$BOTH" == true ]]; then
  log "Creating BOTH prod and dev records for app '${APP_NAME}'..."
  printf '\n'

  prod_record="$(record_name_for_env "$APP_NAME" prod)"
  dev_record="$(record_name_for_env  "$APP_NAME" dev)"

  log "--- PROD ---"
  register_record "$prod_record" "$TARGET" "$ZONE" "$RESOURCE_GROUP" "$TTL"

  log "--- DEV ---"
  register_record "$dev_record"  "$TARGET" "$ZONE" "$RESOURCE_GROUP" "$TTL"

  log "Done. Both records registered."
else
  record="$(record_name_for_env "$APP_NAME" "$ENV")"
  register_record "$record" "$TARGET" "$ZONE" "$RESOURCE_GROUP" "$TTL"
  log "Done."
fi
