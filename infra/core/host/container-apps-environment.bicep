@description('The name of the Container Apps environment')
param name string

@description('The location where the Container Apps environment will be created')
param location string = resourceGroup().location

@description('Tags to be applied to the Container Apps environment')
param tags object = {}

@description('The name of the Log Analytics workspace')
param logAnalyticsWorkspaceName string

@description('The name of the Application Insights component')
param applicationInsightsName string

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: logAnalyticsWorkspaceName
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
    daprAIInstrumentationKey: applicationInsights.properties.InstrumentationKey
    daprAIConnectionString: applicationInsights.properties.ConnectionString
    zoneRedundant: false
  }
}

@description('The resource ID of the Container Apps environment')
output id string = containerAppsEnvironment.id

@description('The name of the Container Apps environment')
output name string = containerAppsEnvironment.name

@description('The default domain of the Container Apps environment')
output defaultDomain string = containerAppsEnvironment.properties.defaultDomain
