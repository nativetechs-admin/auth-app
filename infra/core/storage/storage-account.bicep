@description('The name of the Storage Account')
param name string

@description('The location where the Storage Account will be created')
param location string = resourceGroup().location

@description('Tags to be applied to the Storage Account')
param tags object = {}

@description('The SKU of the Storage Account')
param sku string = 'Standard_LRS'

@description('The principal ID of the managed identity to grant access')
param principalId string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    encryption: {
      requireInfrastructureEncryption: false
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
      }
      keySource: 'Microsoft.Storage'
    }
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    publicNetworkAccess: 'Enabled'
    supportsHttpsTrafficOnly: true
  }
}

// Grant Storage Blob Data Contributor role to the managed identity
resource storageBlobDataContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, principalId, 'Storage Blob Data Contributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

@description('The resource ID of the Storage Account')
output id string = storageAccount.id

@description('The name of the Storage Account')
output name string = storageAccount.name

@description('The primary endpoints of the Storage Account')
output primaryEndpoints object = storageAccount.properties.primaryEndpoints
