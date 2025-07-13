@description('The name of the managed identity')
param name string

@description('The location where the managed identity will be created')
param location string = resourceGroup().location

@description('Tags to be applied to the managed identity')
param tags object = {}

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
  tags: tags
}

@description('The resource ID of the created managed identity')
output id string = managedIdentity.id

@description('The principal ID of the created managed identity')
output principalId string = managedIdentity.properties.principalId

@description('The client ID of the created managed identity')
output clientId string = managedIdentity.properties.clientId

@description('The name of the created managed identity')
output name string = managedIdentity.name
