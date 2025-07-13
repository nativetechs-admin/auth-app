targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string

// Optional parameters with defaults
@description('Flag to use Azure OpenAI service')
param useAOAI bool = false

@description('Location for Azure OpenAI service')
param aoaiLocation string = location

@description('SKU name for Azure OpenAI service')
param aoaiSkuName string = 'S0'

// Generate a unique token for resource naming
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Tags that will be applied to all resources
var tags = {
  'azd-env-name': environmentName
}

// Organize resource names
var abbrs = loadJsonContent('./abbreviations.json')
var resourceGroupName = '${abbrs.resourcesResourceGroups}${environmentName}'

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// Create user-assigned managed identity for secure access
module identity './core/security/managed-identity.bicep' = {
  name: 'identity'
  scope: rg
  params: {
    name: '${abbrs.managedIdentityUserAssignedIdentities}${resourceToken}'
    location: location
    tags: tags
  }
}

// Storage account for application data and logs
module storage './core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    tags: tags
    principalId: identity.outputs.principalId
  }
}

// Log Analytics workspace for monitoring
module logAnalytics './core/monitor/loganalytics.bicep' = {
  name: 'loganalytics'
  scope: rg
  params: {
    name: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: location
    tags: tags
  }
}

// Application Insights for application monitoring
module appInsights './core/monitor/applicationinsights.bicep' = {
  name: 'appinsights'
  scope: rg
  params: {
    name: '${abbrs.insightsComponents}${resourceToken}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalytics.outputs.id
  }
}

// Key Vault for storing sensitive configuration
module keyVault './core/security/keyvault.bicep' = {
  name: 'keyvault'
  scope: rg
  params: {
    name: '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    tags: tags
    principalId: principalId
    identityPrincipalId: identity.outputs.principalId
  }
}

// Container Apps Environment
module containerAppsEnvironment './core/host/container-apps-environment.bicep' = {
  name: 'container-apps-env'
  scope: rg
  params: {
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    tags: tags
    logAnalyticsWorkspaceName: logAnalytics.outputs.name
    applicationInsightsName: appInsights.outputs.name
  }
}

// Container Registry for storing container images
module containerRegistry './core/host/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    name: '${abbrs.containerRegistryRegistries}${resourceToken}'
    location: location
    tags: tags
    identityPrincipalId: identity.outputs.principalId
  }
}

// Backend API (Container App)
module backend './app/backend.bicep' = {
  name: 'backend'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}backend-${resourceToken}'
    location: location
    tags: tags
    identityName: identity.outputs.name
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    keyVaultName: keyVault.outputs.name
    applicationInsightsName: appInsights.outputs.name
    storageAccountName: storage.outputs.name
  }
}

// Frontend (Static Web App)
module frontend './app/frontend.bicep' = {
  name: 'frontend'
  scope: rg
  params: {
    name: '${abbrs.webStaticSites}${resourceToken}'
    location: location
    tags: tags
    backendUrl: backend.outputs.uri
  }
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name

output BACKEND_URI string = backend.outputs.uri
output FRONTEND_URI string = frontend.outputs.uri

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name

output AZURE_KEY_VAULT_NAME string = keyVault.outputs.name
output AZURE_KEY_VAULT_ENDPOINT string = keyVault.outputs.endpoint

output AZURE_STORAGE_ACCOUNT string = storage.outputs.name
output AZURE_STORAGE_ENDPOINT string = storage.outputs.primaryEndpoints.blob
