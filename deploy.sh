#!/bin/bash

# Set default values for environment variables if not already set
: "${AZURE_ENV_NAME:=notification-service-env}"
: "${AZURE_LOCATION:=eastus}"

# Variables
RESOURCE_GROUP="rg-${AZURE_ENV_NAME}"
LOCATION="${AZURE_LOCATION}"
ENVIRONMENT="${AZURE_ENV_NAME}"
APP_SERVICE_PLAN="asp-${AZURE_ENV_NAME}"
API_APP="api-${AZURE_ENV_NAME}"
FUNCTION_APP="func-${AZURE_ENV_NAME}"

# Generate a valid storage account name (lowercase, no hyphens/underscores, max 24 chars)
STORAGE_ACCOUNT="sa${AZURE_ENV_NAME//[-_]/}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT,,}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:0:24}"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy resources using Bicep template
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/azure-deploy.bicep \
  --parameters location=$LOCATION appServicePlanName=$APP_SERVICE_PLAN apiAppName=$API_APP functionAppName=$FUNCTION_APP storageAccountName=$STORAGE_ACCOUNT