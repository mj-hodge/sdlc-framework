// modules/dns-record.bicep
// Reusable DNS CNAME record module for an existing Azure DNS zone
// Usage: module dnsRecord 'modules/dns-record.bicep' = { ... }
//
// NOTE: The DNS zone lives in a separate resource group (rg-dns-gorillacommerce).
// This module uses the `existing` keyword with `scope` to reference it cross-RG.

@description('DNS zone name, e.g. gorillacommerce.ai')
param zoneName string

@description('Resource group containing the DNS zone, e.g. rg-dns-gorillacommerce')
param zoneResourceGroup string

@description('Subdomain to create, e.g. myapp or myapp.dev (no trailing dot)')
param recordName string

@description('CNAME target FQDN, e.g. ca-mcp-myapp.eastus.azurecontainerapps.io')
param targetFqdn string

@description('Time-to-live in seconds')
param ttl int = 3600

// ---------------------------------------------------------------------------
// Reference existing DNS zone (cross-resource-group)
// ---------------------------------------------------------------------------

resource dnsZone 'Microsoft.Network/dnsZones@2018-05-01' existing = {
  name: zoneName
  scope: resourceGroup(zoneResourceGroup)
}

// ---------------------------------------------------------------------------
// CNAME record set
// ---------------------------------------------------------------------------

resource cnameRecord 'Microsoft.Network/dnsZones/CNAME@2018-05-01' = {
  parent: dnsZone
  name: recordName
  properties: {
    TTL: ttl
    CNAMERecord: {
      cname: targetFqdn
    }
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Fully qualified domain name of the created DNS record, e.g. myapp.gorillacommerce.ai')
output fqdn string = '${recordName}.${zoneName}'

@description('Resource ID of the CNAME record set')
output id string = cnameRecord.id
