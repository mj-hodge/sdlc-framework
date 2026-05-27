# Shared Infrastructure Templates

Reusable Bicep modules and GitHub Actions workflows for Azure Container Apps deployments.
Extracted from datalake and advertising-amazon patterns (EPIC-002, STORY-021).

---

## GitHub Actions Workflow Templates

Battle-tested CI/CD workflows based on advertising-amazon's production pipeline (dozens of deploys).

### Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| `deploy.yml` | Push to `main`, manual | Full deploy pipeline: pre-deploy gate, Docker build + ACR push, ACA deploy, smoke test, canary rollback, Teams notification |
| `pre-deploy-gate.yml` | Called by `deploy.yml` | 6 parallel checks (tests, secret scan, CVE audit, health check, frontend build, SRE gate) with emergency bypass |
| `pr-checks.yml` | Pull request | Lightweight checks: unit tests, secret scan, CVE audit |

### Quick Start (Workflows)

```bash
# 1. Copy workflow templates to your project
mkdir -p .github/workflows
cp ~/.sdlc/templates/infra/deploy.yml .github/workflows/
cp ~/.sdlc/templates/infra/pre-deploy-gate.yml .github/workflows/
cp ~/.sdlc/templates/infra/pr-checks.yml .github/workflows/

# 2. Search for all CUSTOMIZE markers and replace with your values
grep -rn "CUSTOMIZE" .github/workflows/

# 3. Replace angle-bracket placeholders
#    <your-acr-name>       -> e.g. acrmyproject
#    <your-image>           -> e.g. mcp-server
#    <your-container-app>   -> e.g. ca-mcp-server
#    <your-resource-group>  -> e.g. rg-myproject-production
#    <your-app>             -> e.g. ca-mcp-server.proudcoast-xxxxx.eastus.azurecontainerapps.io
```

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `AZURE_CLIENT_ID` | Service principal / managed identity client ID for OIDC login |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `GITLEAKS_LICENSE` | (Optional) Gitleaks enterprise license key for PR secret scan |

### Required GitHub Repository Variables

| Variable | Description |
|----------|-------------|
| `TEAMS_WEBHOOK_URL` | (Optional) Microsoft Teams incoming webhook URL for deploy notifications. If not set, notification step is skipped gracefully. |
| `CANARY_ROLLBACK_ENABLED` | Set to `true` to enable automatic rollback when post-deploy smoke test fails. Recommended to enable after first successful deploy. |

### How to Customize

1. **Language/runtime:** Templates default to Python 3.12 + pip. For Node.js, replace `setup-python` with `setup-node` and `pip install` with `npm ci`.

2. **Test commands:** Replace pytest paths in both `pre-deploy-gate.yml` (full suite) and `pr-checks.yml` (fast subset).

3. **Frontend build:** If your project has no frontend, remove the `frontend-build` job from `pre-deploy-gate.yml` and remove it from the `gate-summary` needs list.

4. **SRE gate:** If not using SDLC site-reliability reviews (`scripts/sre-gate.py`), remove the `sre-gate` job from `pre-deploy-gate.yml` and remove it from the `gate-summary` needs list.

5. **Health endpoint:** Adjust the expected fields in the health-check job to match your `/healthz` or `/health` response schema.

6. **Emergency deploy:** Include `[EMERGENCY-DEPLOY]` in a commit message to bypass all gate checks. An audit issue is automatically created. The smoke test still runs post-deploy.

### Design Decisions

- **Version tags, not pinned SHAs:** All `uses:` references use version tags (`@v4`, `@v2`, etc.) for readability and automatic patch updates. Pin to SHAs if your security policy requires it.
- **Teams over Slack:** Teams webhook is simpler (no bot token required) and matches the org's communication stack.
- **Secret scan uses manual gitleaks install in gate, action in PR:** The gate needs SARIF output for artifacts; the PR check uses the official action for simpler setup.
- **CVE audit is non-blocking in PR checks:** `pip-audit || true` prevents blocking PRs on upstream CVEs you cannot fix. The gate treats it as blocking.
- **Canary rollback is opt-in:** Set `CANARY_ROLLBACK_ENABLED=true` only after verifying rollback works in your environment.

---

## Bicep Infrastructure Modules

## Modules

| Module | Resource | Key Parameters |
|--------|----------|---------------|
| `modules/container-app.bicep` | Azure Container App | appName, envId, imageName, cpu, memory, replicas, probes, secrets |
| `modules/container-registry.bicep` | Azure Container Registry | acrName, sku (default: Basic) |
| `modules/key-vault.bicep` | Azure Key Vault | kvName, enableRbac (default: true), softDeleteDays (default: 7) |
| `modules/log-analytics.bicep` | Log Analytics Workspace | name, retentionDays (default: 30) |
| `modules/managed-identity.bicep` | User-Assigned Managed Identity | name |
| `modules/dns-record.bicep` | Azure DNS CNAME Record | zoneName, zoneResourceGroup, recordName, targetFqdn, ttl (default: 3600) |

## Quick Start

```bash
# 1. Copy the template main.bicep to your project
cp ~/.sdlc/templates/infra/main.bicep.template infra/main.bicep
cp -r ~/.sdlc/templates/infra/modules/ infra/modules/

# 2. Replace placeholders (substitute your actual dept-product, e.g. advertising-amazon)
sed -i 's/<dept-product>/advertising-amazon/g' infra/main.bicep
sed -i 's/<deptproduct>/advertisingamazon/g' infra/main.bicep

# 3. Create parameters file
cat > infra/parameters.prod.json << 'EOF'
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "location": { "value": "eastus" },
    "acrName": { "value": "acradvertisingamazon" },
    "imageTag": { "value": "latest" }
  }
}
EOF

# 4. Deploy
az deployment group create \
  --resource-group rg-advertising-amazon-production \
  --template-file infra/main.bicep \
  --parameters @infra/parameters.prod.json
```

## Module Reference

Modules support MCP server or app deployments and are consumed via `main.bicep.template`.

### container-app.bicep

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `appName` | string | — | Container App name |
| `location` | string | — | Azure region |
| `envId` | string | — | Container Apps Environment resource ID |
| `imageName` | string | — | Image without tag (e.g. `acr.azurecr.io/app`) |
| `imageTag` | string | `latest` | Image tag |
| `cpu` | string | `0.5` | vCPU (as string: `'0.5'`, `'1.0'`) |
| `memory` | string | `1Gi` | Memory (e.g. `1Gi`, `2Gi`) |
| `minReplicas` | int | `1` | Min replicas (0 = scale to zero) |
| `maxReplicas` | int | `3` | Max replicas |
| `targetPort` | int | `8000` | Container port |
| `healthPath` | string | `/health` | Liveness probe path |
| `readinessPath` | string | `/health/ready` | Readiness probe path |
| `managedIdentityId` | string | — | User-assigned managed identity resource ID |
| `acrLoginServer` | string | — | ACR login server |
| `envVars` | array | `[]` | Non-secret env vars: `[{name, value}]` |
| `secretRefs` | array | `[]` | Secret env vars: `[{name, secretRef}]` |
| `secrets` | array | `[]` | Secret definitions: `[{name, keyVaultUrl, identity}]` |

Outputs: `fqdn`, `latestRevisionName`

**Probe defaults (matches ACA best practices):**
- Liveness: initialDelay 30s, period 30s, timeout 5s, failure threshold 3
- Readiness: initialDelay 10s, period 15s, timeout 5s, failure threshold 3

### container-registry.bicep

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `acrName` | string | — | Registry name (globally unique, alphanumeric) |
| `location` | string | — | Azure region |
| `sku` | string | `Basic` | `Basic` / `Standard` / `Premium` |
| `adminEnabled` | bool | `false` | Enable admin credentials (prefer managed identity) |

Outputs: `loginServer`, `id`

### key-vault.bicep

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `kvName` | string | — | Vault name (3-24 chars, globally unique) |
| `location` | string | — | Azure region |
| `enableRbac` | bool | `true` | Use RBAC (recommended) vs access policies |
| `softDeleteDays` | int | `7` | Soft-delete retention (7-90 days) |

Outputs: `uri`, `id`

### log-analytics.bicep

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | string | — | Workspace name |
| `location` | string | — | Azure region |
| `retentionDays` | int | `30` | Data retention (30-730 days) |

Outputs: `workspaceId`, `customerId`

### managed-identity.bicep

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | string | — | Identity resource name |
| `location` | string | — | Azure region |

Outputs: `principalId`, `clientId`, `id`

### dns-record.bicep

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `zoneName` | string | — | DNS zone name (e.g. `gorillacommerce.ai`) |
| `zoneResourceGroup` | string | — | Resource group containing the DNS zone |
| `recordName` | string | — | Subdomain record name (e.g. `myapp` or `myapp.dev`) |
| `targetFqdn` | string | — | CNAME target FQDN (e.g. Container App FQDN) |
| `ttl` | int | `3600` | TTL in seconds |

Outputs: `fqdn` (full domain, e.g. `myapp.gorillacommerce.ai`)

**Usage pattern:** DNS zone is centralized in `rg-dns-gorillacommerce`. The module uses `scope: resourceGroup(dnsResourceGroup)` in the parent template to deploy into the DNS resource group, separate from the app's resource group.

## Standard RBAC Roles

Always assign these after deploying identity + ACR + Key Vault:

| Role | GUID | Purpose |
|------|------|---------|
| `AcrPull` | `7f951dda-4ed3-4680-a7ca-43fe172d538d` | Container App pulls images |
| `Key Vault Secrets User` | `4633458b-17de-408a-b874-0445c86b69e6` | Container App reads secrets |
| `Storage Blob Data Reader` | `2a2b9908-6ea1-4ae2-8e65-a410df84e7d1` | Read-only blob access |

Role assignments are defined in `main.bicep.template` — do not put them in modules (scope varies per project).

## Naming Conventions

| Resource | Pattern | Example |
|----------|---------|---------|
| Repository | `{dept}-{product}` | `advertising-amazon` |
| Managed Identity | `id-{dept}-{product}` | `id-advertising-amazon` |
| Log Analytics | `log-{dept}-{product}` | `log-advertising-amazon` |
| Container Registry | `acr{dept}{product}` | `acradvertisingamazon` |
| Key Vault | `kv-{dept}-{product}` | `kv-advertising-amazon` |
| ACA Environment | `cae-{dept}-{product}` | `cae-advertising-amazon` |
| Container App (MCP) | `ca-mcp-{dept}-{product}` | `ca-mcp-advertising-amazon` |
| Container App (Dashboard) | `ca-{dept}-{product}` | `ca-advertising-amazon` |
| Resource Group | `rg-{dept}-{product}-{env}` | `rg-advertising-amazon-production` |
| DNS CNAME (MCP prod) | `mcp-{dept}-{product}` | `mcp-advertising-amazon.gorillacommerce.ai` |
| DNS CNAME (Dashboard prod) | `{dept}-{product}` | `advertising-amazon.gorillacommerce.ai` |
| DNS CNAME (MCP dev) | `mcp-{dept}-{product}.dev` | `mcp-advertising-amazon.dev.gorillacommerce.ai` |
| DNS CNAME (Dashboard dev) | `{dept}-{product}.dev` | `advertising-amazon.dev.gorillacommerce.ai` |

## Health Endpoint Standard

All MCP servers MUST implement both endpoints (enforced by module probe defaults):

- `GET /health` — liveness: returns 200 if process is alive
- `GET /health/ready` — readiness: returns 200 only if all adapters/connections are healthy

ACA uses liveness to restart unhealthy containers and readiness to route traffic.
See cross-project-standards.md for the full health endpoint contract.
