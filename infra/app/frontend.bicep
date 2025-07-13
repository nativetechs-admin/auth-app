@description('The name of the Static Web App for the frontend')
param name string

@description('The location where the Static Web App will be created')
param location string = resourceGroup().location

@description('Tags to be applied to the Static Web App')
param tags object = {}

@description('The SKU of the Static Web App')
param sku string = 'Free'

@description('The backend URL for API proxy')
param backendUrl string

resource staticWebApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'frontend' })
  sku: {
    name: sku
    tier: sku
  }
  properties: {
    buildProperties: {
      appLocation: '/'
      apiLocation: ''
      outputLocation: 'dist'
    }
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    enterpriseGradeCdnStatus: 'Disabled'
  }
}

// Configure API proxy to backend
resource staticWebAppConfig 'Microsoft.Web/staticSites/config@2022-09-01' = {
  name: 'appsettings'
  parent: staticWebApp
  properties: {
    VITE_API_BASE_URL: backendUrl
    VITE_ENVIRONMENT: 'production'
  }
}

@description('The resource ID of the Static Web App')
output id string = staticWebApp.id

@description('The name of the Static Web App')
output name string = staticWebApp.name

@description('The URI of the Static Web App')
output uri string = 'https://${staticWebApp.properties.defaultHostname}'
