// modules/container-registry.bicep
// Reusable Azure Container Registry module
// Usage: module acr 'modules/container-registry.bicep' = { ... }

@description('Name of the Azure Container Registry (must be globally unique, 5-50 alphanumeric)')
param acrName string

@description('Azure region')
param location string

@description('SKU tier: Basic | Standard | Premium')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

@description('Enable admin user credentials (not recommended — use managed identity instead)')
param adminEnabled bool = false

// ---------------------------------------------------------------------------
// Container Registry
// ---------------------------------------------------------------------------

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: adminEnabled
    // Geo-replication requires Premium SKU
    // publicNetworkAccess: 'Enabled' — default, restrict for Premium if needed
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('ACR login server (e.g. acrmcp.azurecr.io)')
output loginServer string = acr.properties.loginServer

@description('ACR resource ID — used for role assignments')
output id string = acr.id
