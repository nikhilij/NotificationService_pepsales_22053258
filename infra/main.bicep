param environmentName string
param location string

// Create a safe name by replacing underscores with hyphens
var safeEnvironmentName = replace(environmentName, '_', '')

// Add Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: 'log-${safeEnvironmentName}-centralus'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// Add Application Insights resource
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${safeEnvironmentName}-centralus'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Request_Source: 'rest'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts@2021-04-15' = {
  name: '${safeEnvironmentName}cosmosdb-centralus'
  location: location
  kind: 'MongoDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
  }
}

resource serviceBus 'Microsoft.ServiceBus/namespaces@2021-06-01-preview' = {
  name: '${safeEnvironmentName}servicebus-centralus'
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
}

resource userAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'identity-${uniqueString(subscription().id, environmentName)}-${location}'
  location: location
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2021-02-01' = {
  name: 'stor${uniqueString(subscription().id, environmentName, location)}'
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
}

resource appService 'Microsoft.Web/sites@2021-02-01' = {
  name: 'app-${uniqueString(subscription().id, environmentName)}-${location}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentity.id}': {}
    }
  }
  tags: {
    'azd-env-name': environmentName
    'azd-service-name': 'api'
  }
  properties: {
    siteConfig: {      cors: {
        allowedOrigins: ['*']
      }
      appSettings: [
        {
          name: 'MONGODB_URI'
          value: 'mongodb+srv://developernikhilsoni973:3wcWtTwF9lcKw7OJ@cluster0.8fbif.mongodb.net/'
        }
        {
          name: 'MONGODB_DATABASE'
          value: 'notification_service'
        }
        {
          name: 'RABBITMQ_URL'
          value: 'amqps://yhqoryfl:GVbio6PSCnUwJX_Im22jdSPni5Z8-Vjv@fly.rmq.cloudamqp.com/yhqoryfl'
        }
        {
          name: 'RABBITMQ_QUEUE'
          value: 'notifications'
        }
        {
          name: 'ENVIRONMENT'
          value: 'production'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
      ]
    }
  }
}

resource functionApp 'Microsoft.Web/sites@2021-02-01' = {
  name: 'function-${uniqueString(subscription().id, environmentName)}-${location}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentity.id}': {}
    }
  }
  tags: {
    'azd-env-name': environmentName
    'azd-service-name': 'consumer'
  }
  properties: {
    siteConfig: {
      appSettings: [
        {          name: 'AzureWebJobsStorage'
          value: storageAccount.properties.primaryEndpoints.blob
        }
        {
          name: 'MONGODB_URI'
          value: 'mongodb+srv://developernikhilsoni973:3wcWtTwF9lcKw7OJ@cluster0.8fbif.mongodb.net/'
        }
        {
          name: 'MONGODB_DATABASE'
          value: 'notification_service'
        }
        {
          name: 'RABBITMQ_URL'
          value: 'amqps://yhqoryfl:GVbio6PSCnUwJX_Im22jdSPni5Z8-Vjv@fly.rmq.cloudamqp.com/yhqoryfl'
        }
        {
          name: 'RABBITMQ_QUEUE'
          value: 'notifications'
        }
        {
          name: 'ENVIRONMENT'
          value: 'production'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
      ]
    }
  }
}

resource roleAssignmentBlobOwner 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(subscription().id, userAssignedIdentity.id, 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b')
  scope: storageAccount
  properties: {
    roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource roleAssignmentBlobContributor 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(subscription().id, userAssignedIdentity.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource roleAssignmentQueueContributor 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(subscription().id, userAssignedIdentity.id, '974c5e8b-45b9-4653-ba55-5f855dd0fb88')
  scope: storageAccount
  properties: {
    roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/974c5e8b-45b9-4653-ba55-5f855dd0fb88'
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource roleAssignmentTableContributor 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(subscription().id, userAssignedIdentity.id, '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3')
  scope: storageAccount
  properties: {
    roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource roleAssignmentMetricsPublisher 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(subscription().id, userAssignedIdentity.id, '3913510d-42f4-4e42-8a64-420c390055eb')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/3913510d-42f4-4e42-8a64-420c390055eb'
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output RESOURCE_GROUP_ID string = resourceGroup().id
