#!/bin/bash

# Variables
RESOURCE_GROUP="rg-${AZURE_ENV_NAME}"
LOCATION="${AZURE_LOCATION}"
ENVIRONMENT="${AZURE_ENV_NAME}"
APP_SERVICE_PLAN="asp-${AZURE_ENV_NAME}"
API_APP="api-${AZURE_ENV_NAME}"
FUNCTION_APP="func-${AZURE_ENV_NAME}"
STORAGE_ACCOUNT="sa${AZURE_ENV_NAME}"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy resources using Bicep template
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file azure-deploy.bicep \
  --parameters location=$LOCATION environment=$ENVIRONMENT appServicePlanName=$APP_SERVICE_PLAN apiAppName=$API_APP functionAppName=$FUNCTION_APP storageAccountName=$STORAGE_ACCOUNT
