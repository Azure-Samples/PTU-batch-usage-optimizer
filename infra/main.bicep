param location string
param namePrefix string // User-defined acronym/prefix
param eventHubConsumerGroupName string
param cosmosDbDatabase string
param cosmosDbContainer string
param azureOpenAiEndpoint string
param azureOpenAiApiKey string
param azureOpenAiDeploymentName string
param azureOpenAiResourceId string
param tenantId string
param clientId string
@secure()
param clientSecret string

// Generate a stable unique suffix per RG
var suffix = uniqueString(resourceGroup().id)
// Truncate suffix to 6 chars to keep names under limits
var shortSuffix = toLower(substring(suffix, 0, 6))

// Derived resource names using shortened suffix
// Derive Cosmos DB account name (lowercase, starts with letter):
var cosmosAccountName = toLower('${namePrefix}cos${shortSuffix}')
var eventHubNamespaceName = '${namePrefix}-ehns-${shortSuffix}'
var eventHubName = '${namePrefix}-eh-${shortSuffix}'
var eventHubAuthRuleName = '${namePrefix}-eh-rule-${shortSuffix}'
var eventHubNamespaceAuthRulePTUSendName = '${namePrefix}-send-listen-${shortSuffix}'
var eventHubNamespaceAuthRuleRootManageName = '${namePrefix}-rootmanage-${shortSuffix}'
var storageAccountName = toLower('${namePrefix}stg${shortSuffix}')
var storageContainerName = '${namePrefix}-checkpoint-${shortSuffix}'
var managedEnvConsumerName = '${namePrefix}-env-cons-${shortSuffix}'
var managedEnvProducerName = '${namePrefix}-env-prod-${shortSuffix}'
var consumerProfile = toLower('${namePrefix}pc${shortSuffix}')  //  prefix+pc+suffix, max 14 chars
var producerProfile = toLower('${namePrefix}pp${shortSuffix}')  //  prefix+pp+suffix
var containerAppConsumerName = '${namePrefix}-ca-cons-${shortSuffix}'
var containerAppProducerName = '${namePrefix}-ca-prod-${shortSuffix}'
var acrName = toLower('${namePrefix}acr${shortSuffix}')
// acrServer remains if needed elsewhere

// Derived Cosmos DB endpoint and key
var cosmosDbEndpoint = cosmosdbAccount.properties.documentEndpoint
var cosmosDbKey = cosmosdbAccount.listKeys().primaryMasterKey

resource managedEnvironment_consumer 'Microsoft.App/managedEnvironments@2025-01-01' = {
  name: managedEnvConsumerName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    appLogsConfiguration: {}
    zoneRedundant: false
    kedaConfiguration: {}
    daprConfiguration: {}
    customDomainConfiguration: {}
    workloadProfiles: [
      {
        workloadProfileType: 'Consumption'
        name: 'Consumption'
      }
      {
        workloadProfileType: 'D4'
        name: consumerProfile
        minimumCount: 1
        maximumCount: 1
      }
    ]
    peerAuthentication: {
      mtls: {
        enabled: false
      }
    }
    peerTrafficConfiguration: {
      encryption: {
        enabled: false
      }
    }
  }
}

resource managedEnvironment_producer 'Microsoft.App/managedEnvironments@2025-01-01' = {
  name: managedEnvProducerName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    appLogsConfiguration: {}
    zoneRedundant: false
    kedaConfiguration: {}
    daprConfiguration: {}
    customDomainConfiguration: {}
    workloadProfiles: [
      {
        workloadProfileType: 'Consumption'
        name: 'Consumption'
      }
      {
        workloadProfileType: 'D4'
        name: producerProfile
        minimumCount: 1
        maximumCount: 1
      }
    ]
    peerAuthentication: {
      mtls: {
        enabled: false
      }
    }
    peerTrafficConfiguration: {
      encryption: {
        enabled: false
      }
    }
  }
}

resource eventHubNamespace 'Microsoft.EventHub/namespaces@2024-05-01-preview' = {
  name: eventHubNamespaceName
  location: location
  tags: {
    SecurityControl: 'Ignore'
  }
  sku: {
    name: 'Standard'
    tier: 'Standard'
    capacity: 1
  }
  properties: {
    geoDataReplication: {
      maxReplicationLagDurationInSeconds: 0
      locations: [
        {
          locationName: location
          roleType: 'Primary'
        }
      ]
    }
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    zoneRedundant: true
    isAutoInflateEnabled: false
    maximumThroughputUnits: 0
    kafkaEnabled: true
  }
}

resource storageAccounts_storptubacthoptckpnt_name_resource 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name: storageAccountName
  location: location
  tags: {
    SecurityControl: 'Ignore'
  }
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    dnsEndpointType: 'Standard'
    defaultToOAuthAuthentication: false
    publicNetworkAccess: 'Enabled'
    allowCrossTenantReplication: false
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    largeFileSharesState: 'Enabled'
    networkAcls: {
      resourceAccessRules: [
        {
          tenantId: tenantId
          resourceId: '/subscriptions/2168a4ef-0538-435e-9ae6-beb6183f2769/providers/Microsoft.Security/datascanners/storageDataScanner'
        }
      ]
      bypass: 'AzureServices'
      virtualNetworkRules: []
      ipRules: []
      defaultAction: 'Allow'
    }
    supportsHttpsTrafficOnly: true
    encryption: {
      requireInfrastructureEncryption: false
      services: {
        file: {
          keyType: 'Account'
          enabled: true
        }
        blob: {
          keyType: 'Account'
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
    accessTier: 'Hot'
  }
}

resource registries_acr_name_resource 'Microsoft.ContainerRegistry/registries@2025-03-01-preview' = {
  name: acrName
  location: location
  tags: {
    SecurityControl: 'Ignore'
  }
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: true
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
      retentionPolicy: {
        days: 7
        status: 'disabled'
      }
      exportPolicy: {
        status: 'enabled'
      }
      azureADAuthenticationAsArmPolicy: {
        status: 'enabled'
      }
      softDeletePolicy: {
        retentionDays: 7
        status: 'disabled'
      }
    }
    encryption: {
      status: 'disabled'
    }
    dataEndpointEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    zoneRedundancy: 'Disabled'
    anonymousPullEnabled: false
    metadataSearch: 'Disabled'
    roleAssignmentMode: 'LegacyRegistryPermissions'
    autoGeneratedDomainNameLabelScope: 'Unsecure'
  }
}

resource registries_acr_name_repositories_admin 'Microsoft.ContainerRegistry/registries/scopeMaps@2025-03-01-preview' = {
  parent: registries_acr_name_resource
  name: '_repositories_admin'
  properties: {
    description: 'Can perform all read, write and delete operations on the registry'
    actions: [
      'repositories/*/metadata/read'
      'repositories/*/metadata/write'
      'repositories/*/content/read'
      'repositories/*/content/write'
      'repositories/*/content/delete'
    ]
  }
}

resource registries_acr_name_repositories_pull 'Microsoft.ContainerRegistry/registries/scopeMaps@2025-03-01-preview' = {
  parent: registries_acr_name_resource
  name: '_repositories_pull'
  properties: {
    description: 'Can pull any repository of the registry'
    actions: [
      'repositories/*/content/read'
    ]
  }
}

resource registries_acr_name_repositories_pull_metadata_read 'Microsoft.ContainerRegistry/registries/scopeMaps@2025-03-01-preview' = {
  parent: registries_acr_name_resource
  name: '_repositories_pull_metadata_read'
  properties: {
    description: 'Can perform all read operations on the registry'
    actions: [
      'repositories/*/content/read'
      'repositories/*/metadata/read'
    ]
  }
}

resource registries_acr_name_repositories_push 'Microsoft.ContainerRegistry/registries/scopeMaps@2025-03-01-preview' = {
  parent: registries_acr_name_resource
  name: '_repositories_push'
  properties: {
    description: 'Can push to any repository of the registry'
    actions: [
      'repositories/*/content/read'
      'repositories/*/content/write'
    ]
  }
}

resource registries_acr_name_repositories_push_metadata_write 'Microsoft.ContainerRegistry/registries/scopeMaps@2025-03-01-preview' = {
  parent: registries_acr_name_resource
  name: '_repositories_push_metadata_write'
  properties: {
    description: 'Can perform all read and write operations on the registry'
    actions: [
      'repositories/*/metadata/read'
      'repositories/*/metadata/write'
      'repositories/*/content/read'
      'repositories/*/content/write'
    ]
  }
}

resource containerApp_consumer 'Microsoft.App/containerapps@2025-01-01' = {
  name: containerAppConsumerName
  location: location
  identity: {
    type: 'None'
  }
  properties: {
    managedEnvironmentId: managedEnvironment_consumer.id
    environmentId: managedEnvironment_consumer.id
    workloadProfileName: consumerProfile
    configuration: {
      activeRevisionsMode: 'Single'
      maxInactiveRevisions: 100
      identitySettings: []
    }
    template: {
      containers: [
        {
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          name: containerAppConsumerName
          env: [
            {
              name: 'EVENTHUB_NAME'
              value: eventHubName
            }
            {
              name: 'STORAGE_ACCOUNT_CHECKPOINT_STORE_CONTAINER'
              value: storageContainerName
            }
            {
              name: 'COSMOSDB_ENDPOINT'
              value: cosmosDbEndpoint
            }
            {
              name: 'COSMOSDB_KEY'
              value: cosmosDbKey
            }
            {
              name: 'COSMOSDB_DATABASE'
              value: cosmosDbDatabase
            }
            {
              name: 'COSMOSDB_CONTAINER'
              value: cosmosDbContainer
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              value: azureOpenAiApiKey
            }
            {
              name: 'AZURE_OPENAI_PTU_DEPLOYMENT_NAME'
              value: azureOpenAiDeploymentName
            }
            {
              name: 'AZURE_OPENAI_RESOURCE_ID'
              value: azureOpenAiResourceId
            }
            {
              name: 'AZURE_TENANT_ID'
              value: tenantId
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: clientId
            }
            {
              name: 'AZURE_CLIENT_SECRET'
              value: clientSecret
            }
          ]
          resources: {
            cpu: 2
            memory: '8Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
        cooldownPeriod: 300
        pollingInterval: 30
      }
    }
  }
}

resource containerApp_producer 'Microsoft.App/containerapps@2025-01-01' = {
  name: containerAppProducerName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: managedEnvironment_producer.id
    environmentId: managedEnvironment_producer.id
    workloadProfileName: producerProfile
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8082
        exposedPort: 0
        transport: 'Auto'
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
        allowInsecure: false
        stickySessions: {
          affinity: 'none'
        }
      }
      maxInactiveRevisions: 100
      identitySettings: []
    }
    template: {
      containers: [
        {
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          name: containerAppProducerName
          env: [
            {
              name: 'EVENTHUB_NAME'
              value: eventHubName
            }
            {
              name: 'STORAGE_ACCOUNT_CHECKPOINT_STORE_CONTAINER'
              value: storageContainerName
            }
            {
              name: 'COSMOSDB_ENDPOINT'
              value: cosmosDbEndpoint
            }
            {
              name: 'COSMOSDB_KEY'
              value: cosmosDbKey
            }
            {
              name: 'COSMOSDB_DATABASE'
              value: cosmosDbDatabase
            }
            {
              name: 'COSMOSDB_CONTAINER'
              value: cosmosDbContainer
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              value: azureOpenAiApiKey
            }
            {
              name: 'AZURE_OPENAI_PTU_DEPLOYMENT_NAME'
              value: azureOpenAiDeploymentName
            }
            {
              name: 'AZURE_OPENAI_RESOURCE_ID'
              value: azureOpenAiResourceId
            }
          ]
          resources: {
            cpu: 2
            memory: '8Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
        cooldownPeriod: 300
        pollingInterval: 30
      }
    }
  }
}

resource namespaces_batchptulab01_name_PTU_Batch_Send 'Microsoft.EventHub/namespaces/authorizationrules@2024-05-01-preview' = {
   parent: eventHubNamespace
  name: eventHubNamespaceAuthRulePTUSendName
  properties: {
    rights: [
      'Manage'
      'Listen'
      'Send'
    ]
  }
}

resource namespaces_batchptulab01_name_RootManageSharedAccessKey 'Microsoft.EventHub/namespaces/authorizationrules@2024-05-01-preview' = {
   parent: eventHubNamespace
  name: eventHubNamespaceAuthRuleRootManageName
  properties: {
    rights: [
      'Listen'
      'Manage'
      'Send'
    ]
  }
}

resource namespaces_batchptulab01_name_ptu_batch 'Microsoft.EventHub/namespaces/eventhubs@2024-05-01-preview' = {
   parent: eventHubNamespace
  name: eventHubName
  properties: {
    messageTimestampDescription: {
      timestampType: 'LogAppend'
    }
    retentionDescription: {
      cleanupPolicy: 'Delete'
      retentionTimeInHours: 24
    }
    messageRetentionInDays: 1
    partitionCount: 1
    status: 'Active'
  }
}

resource namespaces_batchptulab01_name_default 'Microsoft.EventHub/namespaces/networkrulesets@2024-05-01-preview' = {
  parent: eventHubNamespace
  name: 'default'
  properties: {
    publicNetworkAccess: 'Enabled'
    defaultAction: 'Allow'
    virtualNetworkRules: []
    ipRules: []
    trustedServiceAccessEnabled: false
  }
}

resource storageAccounts_storptubacthoptckpnt_name_default 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' = {
  parent: storageAccounts_storptubacthoptckpnt_name_resource
  name: 'default'
  properties: {
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    cors: {
      corsRules: []
    }
    deleteRetentionPolicy: {
      allowPermanentDelete: false
      enabled: true
      days: 7
    }
  }
}

resource Microsoft_Storage_storageAccounts_fileServices_storageAccounts_storptubacthoptckpnt_name_default 'Microsoft.Storage/storageAccounts/fileServices@2024-01-01' = {
  parent: storageAccounts_storptubacthoptckpnt_name_resource
  name: 'default'
  properties: {
    protocolSettings: {
      smb: {}
    }
    cors: {
      corsRules: []
    }
    shareDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

resource Microsoft_Storage_storageAccounts_queueServices_storageAccounts_storptubacthoptckpnt_name_default 'Microsoft.Storage/storageAccounts/queueServices@2024-01-01' = {
  parent: storageAccounts_storptubacthoptckpnt_name_resource
  name: 'default'
  properties: {
    cors: {
      corsRules: []
    }
  }
}

resource Microsoft_Storage_storageAccounts_tableServices_storageAccounts_storptubacthoptckpnt_name_default 'Microsoft.Storage/storageAccounts/tableServices@2024-01-01' = {
  parent: storageAccounts_storptubacthoptckpnt_name_resource
  name: 'default'
  properties: {
    cors: {
      corsRules: []
    }
  }
}

resource namespaces_batchptulab01_name_ptu_batch_ptu_batch_send_listen 'Microsoft.EventHub/namespaces/eventhubs/authorizationrules@2024-05-01-preview' = {
   parent: namespaces_batchptulab01_name_ptu_batch
  name: eventHubAuthRuleName
  properties: {
    rights: [
      'Listen'
      'Send'
    ]
  }  
}

resource namespaces_batchptulab01_name_ptu_batch_Default 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2024-05-01-preview' = {
   parent: namespaces_batchptulab01_name_ptu_batch
  name: eventHubConsumerGroupName
  properties: {}  
}

resource storageAccounts_storptubacthoptckpnt_name_default_ptu_batch_checkpoint 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' = {
   parent: storageAccounts_storptubacthoptckpnt_name_default
  name: storageContainerName
  properties: {
    immutableStorageWithVersioning: {
      enabled: false
    }
    defaultEncryptionScope: '$account-encryption-key'
    denyEncryptionScopeOverride: false
    publicAccess: 'None'
  }  
}

// Cosmos DB resources
// Cosmos DB account
resource cosmosdbAccount 'Microsoft.DocumentDB/databaseAccounts@2022-11-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
  }
}

// Cosmos DB SQL Database
resource cosmosdbSqlDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2022-11-15' = {
  parent: cosmosdbAccount
  name: cosmosDbDatabase
  properties: {
    resource: {
      id: cosmosDbDatabase
    }
    options: {}
  }
}

// Cosmos DB Container
resource cosmosdbContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2022-11-15' = {
  parent: cosmosdbSqlDb
  name: cosmosDbContainer
  properties: {
    resource: {
      id: cosmosDbContainer
      partitionKey: {
        paths: [
          '/id'
        ]
        kind: 'Hash'
      }
    }
    options: {}
  }
}
