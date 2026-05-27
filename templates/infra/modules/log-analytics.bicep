// modules/log-analytics.bicep
// Reusable Log Analytics Workspace module
// Usage: module logs 'modules/log-analytics.bicep' = { ... }

@description('Name of the Log Analytics workspace')
param name string

@description('Azure region')
param location string

@description('Data retention period in days (30-730)')
@minValue(30)
@maxValue(730)
param retentionDays int = 30

// ---------------------------------------------------------------------------
// Log Analytics Workspace
// ---------------------------------------------------------------------------

resource workspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: name
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      // TODO: set dailyQuotaGb to limit cost if needed (e.g. 1.0 for 1 GB/day)
      dailyQuotaGb: -1  // -1 = unlimited
    }
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Log Analytics workspace resource ID')
output workspaceId string = workspace.id

@description('Log Analytics customer ID (used by Container Apps environment)')
output customerId string = workspace.properties.customerId
