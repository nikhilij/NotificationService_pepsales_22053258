param environmentName string
param location string

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts@2021-04-15' = {
  name: '${environmentName}-cosmosdb'
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
  name: '${environmentName}-servicebus'
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
}

resource userAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'identity-${uniqueString(subscription().id, environmentName)}'
  location: location
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2021-02-01' = {
  name: 'storage${uniqueString(subscription().id, environmentName)}'
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
}

resource appService 'Microsoft.Web/sites@2021-02-01' = {
  name: 'app-${uniqueString(subscription().id, environmentName)}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentity.id}': {}
    }
  }
  tags: {
    'azd-env-name': environmentName
  }
  properties: {
    siteConfig: {
      cors: {
        allowedOrigins: ['*']
      }
    }
  }
}

resource functionApp 'Microsoft.Web/sites@2021-02-01' = {
  name: 'function-${uniqueString(subscription().id, environmentName)}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentity.id}': {}
    }
  }
  tags: {
    'azd-env-name': environmentName
  }
  properties: {
    siteConfig: {
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: storageAccount.properties.primaryEndpoints.blob
        }
      ]
    }
  }
}

resource roleAssignmentBlobOwner 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(subscription().id, userAssignedIdentity.id, 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b')
  scope: storageAccount
  properties: {
    roleDefinitionId: '/subscriptions/${subscription().id}/providers/Microsoft.Authorization/roleDefinitions/b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
    principalId: userAssignedIdentity.properties.principalId
  }
}

resource roleAssignmentBlobContributor 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(subscription().id, userAssignedIdentity.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: '/subscriptions/${subscription().id}/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalId: userAssignedIdentity.properties.principalId
  }
}

resource roleAssignmentQueueContributor 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(subscription().id, userAssignedIdentity.id, '974c5e8b-45b9-4653-ba55-5f855dd0fb88')
  scope: storageAccount
  properties: {
    roleDefinitionId: '/subscriptions/${subscription().id}/providers/Microsoft.Authorization/roleDefinitions/974c5e8b-45b9-4653-ba55-5f855dd0fb88'
    principalId: userAssignedIdentity.properties.principalId
  }
}

resource roleAssignmentTableContributor 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(subscription().id, userAssignedIdentity.id, '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3')
  scope: storageAccount
  properties: {
    roleDefinitionId: '/subscriptions/${subscription().id}/providers/Microsoft.Authorization/roleDefinitions/0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
    principalId: userAssignedIdentity.properties.principalId
  }
}

resource roleAssignmentMetricsPublisher 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(subscription().id, userAssignedIdentity.id, '3913510d-42f4-4e42-8a64-420c390055eb')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: '/subscriptions/${subscription().id}/providers/Microsoft.Authorization/roleDefinitions/3913510d-42f4-4e42-8a64-420c390055eb'
    principalId: userAssignedIdentity.properties.principalId
  }
}

output RESOURCE_GROUP_ID string = resourceGroup().id
