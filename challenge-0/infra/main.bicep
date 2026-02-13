// ============================================================================
// Web Search Agent Hack - Infrastructure Deployment
// ============================================================================
// This template deploys all Azure resources needed for the hackathon:
// - Azure OpenAI with gpt-4 deployment (supports web_search_preview)
// - Azure AI Foundry Hub and Project
// - Azure Container Registry
// - Azure Container Apps Environment
// - Storage Account for AI Foundry
// ============================================================================

@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name for all resources')
param baseName string = 'websearchhack'

@description('Unique suffix for globally unique names')
param uniqueSuffix string = uniqueString(resourceGroup().id)

// ============================================================================
// Variables
// ============================================================================

var openAiName = 'openai-${baseName}'
var storageAccountName = 'st${baseName}${uniqueSuffix}'
var containerRegistryName = 'acr${baseName}${uniqueSuffix}'
var containerAppEnvName = 'cae-${baseName}'
var aiHubName = 'hub-${baseName}'
var aiProjectName = 'project-${baseName}'
var logAnalyticsName = 'log-${baseName}'

// ============================================================================
// Log Analytics Workspace (required for Container Apps)
// ============================================================================

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// ============================================================================
// Storage Account (required for AI Foundry)
// ============================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}

// ============================================================================
// Azure OpenAI
// ============================================================================

resource openAi 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
  }
}

// Deploy GPT-4 model (required for web_search_preview)
resource gpt4Deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAi
  name: 'gpt-4-1'
  sku: {
    name: 'GlobalStandard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4'
      version: '0125-Preview'
    }
    raiPolicyName: 'Microsoft.Default'
  }
}

// ============================================================================
// Azure Container Registry
// ============================================================================

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// ============================================================================
// Azure Container Apps Environment
// ============================================================================

resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// ============================================================================
// Azure AI Foundry Hub
// ============================================================================

resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: aiHubName
  location: location
  kind: 'Hub'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'Web Search Agent Hub'
    storageAccount: storageAccount.id
    publicNetworkAccess: 'Enabled'
  }
}

// ============================================================================
// Azure AI Foundry Project
// ============================================================================

resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: aiProjectName
  location: location
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'Web Search Agent Project'
    hubResourceId: aiHub.id
    publicNetworkAccess: 'Enabled'
  }
}

// ============================================================================
// Outputs
// ============================================================================

output resourceGroupName string = resourceGroup().name
output openAiName string = openAi.name
output openAiEndpoint string = openAi.properties.endpoint
output containerRegistryName string = containerRegistry.name
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerAppEnvName string = containerAppEnv.name
output aiHubName string = aiHub.name
output aiProjectName string = aiProject.name
output storageAccountName string = storageAccount.name
