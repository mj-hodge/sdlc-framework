// modules/container-app.bicep
// Reusable Azure Container App module for MCP servers
// Usage: module containerApp 'modules/container-app.bicep' = { ... }

@description('Name of the Container App')
param appName string

@description('Azure region')
param location string

@description('Container Apps Environment resource ID')
param envId string

@description('Container image name (without tag), e.g. acrmcp.azurecr.io/mcp-server')
param imageName string

@description('Container image tag to deploy')
param imageTag string = 'latest'

@description('vCPU allocation (e.g. 0.5, 1.0)')
param cpu string = '0.5'

@description('Memory allocation (e.g. 1Gi, 2Gi)')
param memory string = '1Gi'

@description('Minimum number of replicas (0 = scale to zero)')
param minReplicas int = 1

@description('Maximum number of replicas')
param maxReplicas int = 3

@description('Container port the app listens on')
param targetPort int = 8000

@description('HTTP path for liveness probe')
param healthPath string = '/health'

@description('HTTP path for readiness probe')
param readinessPath string = '/health/ready'

@description('User-assigned managed identity resource ID')
param managedIdentityId string

@description('Environment variables to inject (name/value pairs, non-secret)')
param envVars array = []
// Example:
// envVars: [
//   { name: 'LOG_LEVEL', value: 'INFO' }
//   { name: 'APP_NAME', value: 'mcp-server' }
// ]

@description('Secret references (name/secretRef pairs from configuration.secrets)')
param secretRefs array = []
// Example:
// secretRefs: [
//   { name: 'MY_SECRET', secretRef: 'my-kv-secret' }
// ]

@description('Secrets to define in configuration.secrets (name/keyVaultUrl/identity triples)')
param secrets array = []
// Example:
// secrets: [
//   {
//     name: 'my-kv-secret'
//     keyVaultUrl: 'https://kv-example.vault.azure.net/secrets/my-secret'
//     identity: managedIdentityId
//   }
// ]

@description('ACR login server (e.g. acrmcp.azurecr.io)')
param acrLoginServer string

// ---------------------------------------------------------------------------
// Build combined env array: non-secret vars + secret refs
// ---------------------------------------------------------------------------

var secretEnvVars = [for ref in secretRefs: {
  name: ref.name
  secretRef: ref.secretRef
}]

var allEnvVars = concat(envVars, secretEnvVars)

// ---------------------------------------------------------------------------
// Container App
// ---------------------------------------------------------------------------

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: envId
    configuration: {
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: acrLoginServer
          identity: managedIdentityId
        }
      ]
      secrets: secrets
    }
    template: {
      containers: [
        {
          name: appName
          image: '${imageName}:${imageTag}'
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: allEnvVars
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: healthPath
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: readinessPath
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 15
              timeoutSeconds: 5
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Fully qualified domain name of the container app')
output fqdn string = containerApp.properties.configuration.ingress.fqdn

@description('Name of the latest revision')
output latestRevisionName string = containerApp.properties.latestRevisionName
