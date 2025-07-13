@description('The name of the Application Insights component')
param name string

@description('The location where the Application Insights component will be created')
param location string = resourceGroup().location

@description('Tags to be applied to the Application Insights component')
param tags object = {}

@description('The resource ID of the Log Analytics workspace')
param logAnalyticsWorkspaceId string

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspaceId
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

@description('The resource ID of the Application Insights component')
output id string = applicationInsights.id

@description('The name of the Application Insights component')
output name string = applicationInsights.name

@description('The instrumentation key of the Application Insights component')
output instrumentationKey string = applicationInsights.properties.InstrumentationKey

@description('The connection string of the Application Insights component')
output connectionString string = applicationInsights.properties.ConnectionString
