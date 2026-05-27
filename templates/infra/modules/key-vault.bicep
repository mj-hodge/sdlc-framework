// modules/key-vault.bicep
// Reusable Azure Key Vault module
// Usage: module kv 'modules/key-vault.bicep' = { ... }

@description('Name of the Key Vault (3-24 alphanumeric + hyphens, globally unique)')
param kvName string

@description('Azure region')
param location string

@description('Use RBAC authorization (recommended). Set false only for legacy access policies.')
param enableRbac bool = true

@description('Soft-delete retention period in days (7-90)')
@minValue(7)
@maxValue(90)
param softDeleteDays int = 7

// ---------------------------------------------------------------------------
// Key Vault
// ---------------------------------------------------------------------------

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: kvName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: enableRbac
    enableSoftDelete: true
    softDeleteRetentionInDays: softDeleteDays
    // Restrict deployment access — secrets only via RBAC
    enabledForDeployment: false
    enabledForTemplateDeployment: false
    enabledForDiskEncryption: false
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Key Vault URI for secret references (e.g. in Container Apps secrets)')
output uri string = keyVault.properties.vaultUri

@description('Key Vault resource ID — used for RBAC role assignments')
output id string = keyVault.id
