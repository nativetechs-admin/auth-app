@description('The name of the Log Analytics workspace')
param name string

@description('The location where the Log Analytics workspace will be created')
param location string = resourceGroup().location

@description('Tags to be applied to the Log Analytics workspace')
param tags object = {}

@description('The SKU of the Log Analytics workspace')
param sku string = 'PerGB2018'

@description('The retention period in days')
param retentionInDays int = 30

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: sku
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      dailyQuotaGb: 1
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

@description('The resource ID of the Log Analytics workspace')
output id string = logAnalyticsWorkspace.id

@description('The name of the Log Analytics workspace')
output name string = logAnalyticsWorkspace.name

@description('The customer ID of the Log Analytics workspace')
output customerId string = logAnalyticsWorkspace.properties.customerId
