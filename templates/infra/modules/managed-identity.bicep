// modules/managed-identity.bicep
// Reusable User-Assigned Managed Identity module
// Usage: module identity 'modules/managed-identity.bicep' = { ... }
//
// After deployment, assign roles externally with az role assignment create:
//   az role assignment create \
//     --assignee <principalId> \
//     --role "AcrPull" \
//     --scope <acrId>
//   az role assignment create \
//     --assignee <principalId> \
//     --role "Key Vault Secrets User" \
//     --scope <kvId>

@description('Name of the managed identity resource')
param name string

@description('Azure region')
param location string

// ---------------------------------------------------------------------------
// User-Assigned Managed Identity
// ---------------------------------------------------------------------------

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Object (principal) ID — used for Azure RBAC role assignments')
output principalId string = identity.properties.principalId

@description('Client ID — used in SQL ActiveDirectoryDefault connections and SDK config')
output clientId string = identity.properties.clientId

@description('Resource ID — referenced in Container App identity block and ACR pull config')
output id string = identity.id
