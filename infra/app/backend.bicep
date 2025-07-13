@description('The name of the Container App for the backend')
param name string

@description('The location where the Container App will be created')
param location string = resourceGroup().location

@description('Tags to be applied to the Container App')
param tags object = {}

@description('The name of the managed identity')
param identityName string

@description('The name of the Container Apps environment')
param containerAppsEnvironmentName string

@description('The name of the Container Registry')
param containerRegistryName string

@description('The name of the Key Vault')
param keyVaultName string

@description('The name of the Application Insights component')
param applicationInsightsName string

@description('The name of the Storage Account')
param storageAccountName string

@description('Exists check for the container registry')
param containerRegistryExists bool = true

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: identityName
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppsEnvironmentName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = if (containerRegistryExists) {
  name: containerRegistryName
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'backend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        corsPolicy: {
          allowedOrigins: ['*']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          allowCredentials: true
        }
      }
      registries: containerRegistryExists ? [
        {
          server: containerRegistry.properties.loginServer
          identity: identity.id
        }
      ] : []
      secrets: [
        {
          name: 'azure-client-secret'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-client-secret'
          identity: identity.id
        }
        {
          name: 'secret-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/secret-key'
          identity: identity.id
        }
        {
          name: 'database-url'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/database-url'
          identity: identity.id
        }
      ]
    }
    template: {
      containers: [
        {
          image: containerRegistryExists ? '${containerRegistry.properties.loginServer}/backend:latest' : 'nginx:latest'
          name: 'backend'
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: ''
            }
            {
              name: 'AZURE_CLIENT_SECRET'
              secretRef: 'azure-client-secret'
            }
            {
              name: 'AZURE_TENANT_ID'
              value: ''
            }
            {
              name: 'SECRET_KEY'
              secretRef: 'secret-key'
            }
            {
              name: 'DATABASE_URL'
              secretRef: 'database-url'
            }
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'DEBUG'
              value: 'false'
            }
            {
              name: 'SESSION_COOKIE_SECURE'
              value: 'true'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: applicationInsights.properties.ConnectionString
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

@description('The resource ID of the Container App')
output id string = containerApp.id

@description('The name of the Container App')
output name string = containerApp.name

@description('The URI of the Container App')
output uri string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
