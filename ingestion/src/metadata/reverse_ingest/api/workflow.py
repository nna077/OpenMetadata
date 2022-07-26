"""
Workflow definition for Pushing Metadata such as table description
back to the database service that ingested the metadata, reserved when OM is the source of truth.
"""
from pydantic import ValidationError
from copy import deepcopy

from sqlalchemy.orm.session import Session

from metadata.config.workflow import fetch_type_class, get_class
from metadata.ingestion.api.processor import Processor
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.ingestion.source.database.common_db_source import SQLSourceStatus

from metadata.generated.schema.metadataIngestion.workflow import OpenMetadataWorkflowConfig
from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import OpenMetadataConnection
from metadata.generated.schema.metadataIngestion.reverseIngestDatabaseServicePipeline import ReverseIngestDatabaseServicePipeline
from metadata.generated.schema.entity.data.table import Table
from metadata.generated.schema.entity.data.database import Database
from metadata.generated.schema.metadataIngestion.workflow import (
    Processor as WorkflowProcessor,
)
from metadata.reverse_ingest.processor.database.common_db_processor import CommonDbProcessor
from metadata.utils.logger import reverse_logger
from metadata.utils.connections import (
    create_and_bind_session,
    get_connection,
    test_connection,
)

from metadata.reverse_ingest.processor.reverse import ReverseProcessor

logger = reverse_logger()

class ReverseWorkflow:
    """
    Configure and update the metadata back to the Database Service
    For now, only database, table, and column description are supported.
    """

    processor : Processor
    config: OpenMetadataWorkflowConfig
    metadata: OpenMetadata

    def __init__(self, config: OpenMetadataWorkflowConfig) -> None:
        self.config = config
        self.metadata_config: OpenMetadataConnection = (
            self.config.workflowConfig.openMetadataServerConfig
        )
        # Prepare the connection to the database service
        self.source_config : ReverseIngestDatabaseServicePipeline = (
            self.config.source.sourceConfig.config
        )
        self.source_status = SQLSourceStatus()

        self.processor = None

        # OpenMetadata client to fetch entities
        self.metadata = OpenMetadata(self.metadata_config)

    @classmethod
    def create(cls, config_dict) -> "ReverseWorkflow":
        """
        Parse the JSON dictionary and create the Egestion Workflow
        """
        try:
            config = OpenMetadataWorkflowConfig.parse_obj(config_dict)
            return cls(config)
        except ValidationError as err:
            logger.error("Error trying to parse the Ejection Workflow configuration")
            raise err

    def get_processor(
        self,
        processor_type: str,
        service_type: str,
        session: Session,
        metadata: OpenMetadata,
        _from: str = "reverse_ingest",
    ) -> Processor:
        a = 1
        processor_class = get_class(
            "metadata.{}.processor.database.{}.{}Processor".format(
                _from,
                service_type,
                service_type.capitalize(),
            )
        ) # metadata.{reverse_ingest}.processor.database.{ServiceType}.{ServiceTypeProcessor}

        processor: CommonDbProcessor = processor_class.create(session, metadata, self.config.source.serviceName)

        logger.debug(f"Type: {processor_type}, {processor_class} configured")

        return processor

    def create_engine_for_session(self, service_connection_config):
        """Create SQLAlchemy engine to use with a session object"""
        engine = get_connection(service_connection_config)
        test_connection(engine)

        return engine

    def create_processor(self, service_connection_config):
        self.processor : CommonDbProcessor = self.get_processor(
            processor_type=self.config.processor.type,  # orm-profiler
            service_type=self.config.source.type,
            metadata=self.metadata,
            # Pass the session as kwargs for the profiler
            session=create_and_bind_session(
                self.create_engine_for_session(service_connection_config)
            )
        )

    def execute(self):
        """
        Create the trino connection and run the ejection back to trino
        """
        copy_service_connection_config = deepcopy(
            self.config.source.serviceConnection.__root__.config
        )
        # create the processor
        self.create_processor(copy_service_connection_config)

        self.processor.process()

        # output the result of the outgest

    def stop(self):
        self.processor.close()
        self.metadata.close()

    # def get_database_entities(self):
    #     """List all databases in service"""

    #     for database in self.metadata.list_all_entities(
    #         entity=Database,
    #         params={"service": self.config.source.serviceName},
    #     ):
    #         yield database

    # def get_table_entities(self, database):
    #     """
    #     List OpenMetadata tables based on the
    #     source configuration.

    #     The listing will be based on the entities from the
    #     informed service name in the source configuration.

    #     Note that users can specify `table_filter_pattern` to
    #     either be `includes` or `excludes`. This means
    #     that we will either what is specified in `includes`
    #     or we will use everything but the tables excluded.

    #     Same with `schema_filter_pattern`.
    #     """
    #     all_tables = self.metadata.list_all_entities(
    #         entity=Table,
    #         params={
    #             "database": self.config.source.serviceName + "." + database.name.__root__
    #         }
    #     )
    #     for table_entity in all_tables:
    #         yield table_entity
