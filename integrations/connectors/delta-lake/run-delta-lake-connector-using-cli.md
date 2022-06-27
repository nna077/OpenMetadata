---
description: Use the 'metadata' CLI to run a one-time ingestion
---

# Run Delta Lake Connector using CLI

Configure and schedule Delta Lake **metadata**, and **profiler** workflows using CLI.

* [Requirements](run-delta-lake-connector-using-cli.md#requirements)
* [Metadata Ingestion](run-delta-lake-connector-using-cli.md#metadata-ingestion)
* [Data Profiler and Quality Tests](run-delta-lake-connector-using-cli.md#data-profiler-and-quality-tests)
* [DBT Integration](run-delta-lake-connector-using-cli.md#dbt-integration)

## Requirements

Follow this [guide](../../../docs/integrations/airflow/) to learn how to set up Airflow to run the metadata ingestions.

### Python requirements

To run the Delta Lake ingestion, you will need to install:

```
pip3 install 'openmetadata-ingestion[deltalake]'
```

## Metadata Ingestion

All connectors are now defined as JSON Schemas. [Here](https://github.com/open-metadata/OpenMetadata/blob/main/catalog-rest-service/src/main/resources/json/schema/entity/services/connections/database/deltaLakeConnection.json) you can find the structure to create a connection to Delta Lake.

In order to create and run a Metadata Ingestion workflow, we will follow the steps to create a JSON configuration able to connect to the source, process the Entities if needed, and reach the OpenMetadata server.

The workflow is modeled around the following [JSON Schema](https://github.com/open-metadata/OpenMetadata/blob/main/catalog-rest-service/src/main/resources/json/schema/metadataIngestion/workflow.json).

### 1. Define the JSON Config

This is a sample config for Delta Lake:

```json
{
  "source": {
    "type": "deltalake",
    "serviceName": "<service name>",
    "serviceConnection": {
      "config": {
        // Either of metastoreHostPort or metastoreFilePath is required
        "metastoreHostPort": "<metastore host port>",
        "metastoreFilePath":"<path_to_metastore>/metastore_db",
        "appName": "MyApp"
      }
    },
    "sourceConfig": {
      "config": {
        "enableDataProfiler": true or false,
        "markDeletedTables": true or false,
        "includeTables": true or false,
        "includeViews": true or false,
        "generateSampleData": true or false,
        "sampleDataQuery": "<query to fetch table data>",
        "schemaFilterPattern": "<schema name regex list>",
        "tableFilterPattern": "<table name regex list>",
        "dbtConfigSource": "<configs for gcs, s3, local or file server to get the DBT files"
      }
    }
  },
  "sink": {
    "type": "metadata-rest",
    "config": {}
  },
  "workflowConfig": {
    "openMetadataServerConfig": {
      "hostPort": "<OpenMetadata host and port>",
      "authProvider": "<OpenMetadata auth provider>"
    }
  }
}
```

#### Source Configuration - Service Connection

You can find all the definitions and types for the `serviceConnection` [here](https://github.com/open-metadata/OpenMetadata/blob/main/catalog-rest-service/src/main/resources/json/schema/entity/services/connections/database/deltaLakeConnection.json).

* **metastoreHostPort** (Optional): Enter the Host & Port of Hive Metastore to establish a sparks session.
* **metastoreFilePath** (Optional): Enter the file path to local Metastore incase sparks cluster is running locally.
* **appName** (Optional): Enter the app name of spark session.
* **connectionOptions** (Optional): Enter the details for any additional connection options that can be sent to Delta Lake during the connection. These details must be added as Key-Value pairs.
* **connectionArguments** (Optional): Enter the details for any additional connection arguments such as security or protocol configs that can be sent to Delta Lake during the connection. These details must be added as Key-Value pairs.

#### Source Configuration - Source Config

The `sourceConfig` is defined [here](https://github.com/open-metadata/OpenMetadata/blob/main/catalog-rest-service/src/main/resources/json/schema/metadataIngestion/databaseServiceMetadataPipeline.json).

* **enableDataProfiler**: \*\*\*\* `true` or `false`, to run the profiler (not the tests) during the metadata ingestion.
* **markDeletedTables**: To flag tables as soft-deleted if they are not present anymore in the source system.
* **includeTables**: `true` or `false`, to ingest table data. Default is true.
* **includeViews**: `true` or `false`, to ingest views definitions.
* **generateSampleData**: To ingest sample data based on `sampleDataQuery`.
* **sampleDataQuery**: Defaults to `select * from {}.{} limit 50`.
* **schemaFilterPattern** and **tableFilterPattern**: Note that the `schemaFilterPattern` and `tableFilterPattern` both support regex as `include` or `exclude`. E.g.,

```
"tableFilterPattern": {
  "includes": ["users", "type_test"]
}
```

#### Sink Configuration

To send the metadata to OpenMetadata, it needs to be specified as `"type": "metadata-rest"`.

#### Workflow Configuration

The main property here is the `openMetadataServerConfig`, where you can define the host and security provider of your OpenMetadata installation.

For a simple, local installation using our docker containers, this looks like:

```
"workflowConfig": {
  "openMetadataServerConfig": {
    "hostPort": "http://localhost:8585/api",
    "authProvider": "no-auth"
  }
}
```

#### OpenMetadata Security Providers

We support different security providers. You can find their definitions [here](https://github.com/open-metadata/OpenMetadata/tree/main/catalog-rest-service/src/main/resources/json/schema/security/client). An example of an Auth0 configuration would be the following:

```
"workflowConfig": {
    "openMetadataServerConfig": {
        "hostPort": "http://localhost:8585/api",
        "authProvider": "auth0",
        "securityConfig": {
            "clientId": "<client ID>",
            "secretKey": "<secret key>",
            "domain": "<domain>"
        }
    }
}
```

### 2. Run with the CLI

First, we will need to save the JSON file. Afterward, and with all requirements installed, we can run:

```
metadata ingest -c <path-to-json>
```

Note that from connector to connector, this recipe will always be the same. By updating the JSON configuration, you will be able to extract metadata from different sources.

## Data Profiler and Quality Tests

The Data Profiler workflow will be using the `orm-profiler` processor. While the `serviceConnection` will still be the same to reach the source system, the `sourceConfig` will be updated from previous configurations.

### 1. Define the JSON configuration

This is a sample config for a Snowflake profiler:

```json
{
  "source": {
    "type": "deltalake",
    "serviceName": "<service name>",
    "serviceConnection": {
      "config": {
        // Either of metastoreHostPort or metastoreFilePath is required
        "metastoreHostPort": "<metastore host port>",
        "metastoreFilePath":"<path_to_metastore>/metastore_db",
        "appName": "MyApp"
      }
    },
    "sourceConfig": {
      "config": {
        "type": "Profiler",
        "fqnFilterPattern": "<table FQN filtering regex>"
      }
    }
  },
  "processor": {
    "type": "orm-profiler",
    "config": {}
  },
  "sink": {
    "type": "metadata-rest",
    "config": {}
  },
  "workflowConfig": {
    "openMetadataServerConfig": {
      "hostPort": "<OpenMetadata host and port>",
      "authProvider": "<OpenMetadata auth provider>"
    }
  }
}
```

#### Source Configuration

* You can find all the definitions and types for the `serviceConnection` [here](https://github.com/open-metadata/OpenMetadata/blob/main/catalog-rest-service/src/main/resources/json/schema/entity/services/connections/database/deltaLakeConnection.json).
* The `sourceConfig` is defined [here](https://github.com/open-metadata/OpenMetadata/blob/main/catalog-rest-service/src/main/resources/json/schema/metadataIngestion/databaseServiceProfilerPipeline.json). If you don't need to add any `fqnFilterPattern`, the `"type": "Profiler"` is still required to be present.

Note that the `fqnFilterPattern` supports regex as `include` or `exclude`. E.g.,

```
"fqnFilterPattern": {
  "includes": ["service.database.schema.*"]
}
```

#### Processor

To choose the `orm-profiler`. It can also be updated to define tests from the JSON itself instead of the UI:

```json
 "processor": {
    "type": "orm-profiler",
    "config": {
        "test_suite": {
            "name": "<Test Suite name>",
            "tests": [
                {
                    "table": "<Table FQN>",
                    "table_tests": [
                        {
                            "testCase": {
                                "config": {
                                    "value": 100
                                },
                                "tableTestType": "tableRowCountToEqual"
                            }
                        }
                    ],
                    "column_tests": [
                        {
                            "columnName": "<Column Name>",
                            "testCase": {
                                "config": {
                                    "minValue": 0,
                                    "maxValue": 99
                                },
                                "columnTestType": "columnValuesToBeBetween"
                            }
                        }
                    ]
                }
            ]
        }
     }
  },
```

`tests` is a list of test definitions that will be applied to `table`, informed by its FQN. For each table, one can then define a list of `table_tests` and `column_tests`. Review the supported tests and their definitions to learn how to configure the different cases [here](../../../data-quality/data-quality-overview/tests.md).

#### Workflow Configuration

The same as the [metadata](run-delta-lake-connector-using-cli.md#workflow-configuration) ingestion.

### 2. Run with the CLI

Again, we will start by saving the JSON file.

Then, we can run the workflow as:

```
metadata profile -c <path-to-json>
```

Note how instead of running `ingest`, we are using the `profile` command to select the `Profiler` workflow.

## DBT Integration

You can learn more about how to ingest DBT models' definitions and their lineage [here](../../../data-lineage/dbt-integration/).