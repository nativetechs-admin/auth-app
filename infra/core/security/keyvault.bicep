@description('The name of the Key Vault')
param name string

@description('The location where the Key Vault will be created')
param location string = resourceGroup().location

@description('Tags to be applied to the Key Vault')
param tags object = {}

@description('The principal ID of the user or service principal to grant access')
param principalId string

@description('The principal ID of the managed identity to grant access')
param identityPrincipalId string

@description('Enable soft delete for the Key Vault')
param enableSoftDelete bool = true

@description('Enable purge protection for the Key Vault')
param enablePurgeProtection bool = true

@description('The retention period for soft delete in days')
param softDeleteRetentionInDays int = 90

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenant().tenantId
    enableSoftDelete: enableSoftDelete
    enablePurgeProtection: enablePurgeProtection
    softDeleteRetentionInDays: softDeleteRetentionInDays
    enableRbacAuthorization: true
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow' // In production, consider restricting to specific networks
    }
  }
}

// Grant Key Vault Secrets User role to the user/service principal
resource userSecretsRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, principalId, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: principalId
    principalType: 'User'
  }
}

// Grant Key Vault Secrets User role to the managed identity
resource identitySecretsRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, identityPrincipalId, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: identityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

@description('The resource ID of the Key Vault')
output id string = keyVault.id

@description('The name of the Key Vault')
output name string = keyVault.name

@description('The endpoint of the Key Vault')
output endpoint string = keyVault.properties.vaultUri
