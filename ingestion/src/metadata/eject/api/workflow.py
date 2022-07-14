"""
Workflow definition for the Egestion

"""
from pydantic import ValidationError
from copy import deepcopy
from typing import Iterable, List
from metadata.config.workflow import get_processor

from metadata.utils.filters import filter_by_fqn
from metadata.ingestion.api.processor import Processor
from metadata.generated.schema.metadataIngestion.workflow import OpenMetadataWorkflowConfig
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import OpenMetadataConnection
from metadata.generated.schema.metadataIngestion.trinoServiceEjectPipeline import TrinoServiceEjectPipeline
from metadata.ingestion.source.database.common_db_source import SQLSourceStatus
from metadata.utils.logger import eject_logger
from metadata.generated.schema.entity.data.table import Table
from metadata.generated.schema.entity.data.database import Database
from metadata.utils import fqn
from metadata.utils.connections import (
    create_and_bind_session,
    get_connection,
    test_connection,
)
from metadata.eject.processor.eject import EjectProcessor

logger = eject_logger()

class EjectWorkflow:
    """
    Configure and run the Egestion back to Trino service
    """

    processor : Processor
    config: OpenMetadataWorkflowConfig
    metadata: OpenMetadata

    def __init__(self, config: OpenMetadataWorkflowConfig) -> None:
        self.config = config
        self.metadata_config: OpenMetadataConnection = (
            self.config.workflowConfig.openMetadataServerConfig
        )
        # Prepare the connection to the trino service
        self.source_config : TrinoServiceEjectPipeline = (
            self.config.source.sourceConfig.config
        )
        self.source_status = SQLSourceStatus()

        self.processor = None

        # OpenMetadata client to fetch tables
        self.metadata = OpenMetadata(self.metadata_config)

    @classmethod
    def create(cls, config_dict) -> "EjectWorkflow":
        """
        Parse the JSON dictionary and create the Egestion Workflow
        """
        try:
            config = OpenMetadataWorkflowConfig.parse_obj(config_dict)
            # source_type = config.source.type.lower()
            # if source_type != 'trino': # look back
            #     raise ValidationError
            return cls(config)
        except ValidationError as err:
            logger.error("Error trying to parse the Ejection Workflow configuration")
            raise err

    def get_database_entities(self):
        """List all databases in service"""

        for database in self.metadata.list_all_entities(
            entity=Database,
            params={"service": self.config.source.serviceName},
        ):
            yield database

    def get_table_entities(self, database):
        """
        List OpenMetadata tables based on the
        source configuration.

        The listing will be based on the entities from the
        informed service name in the source configuration.

        Note that users can specify `table_filter_pattern` to
        either be `includes` or `excludes`. This means
        that we will either what is specified in `includes`
        or we will use everything but the tables excluded.

        Same with `schema_filter_pattern`.
        """
        all_tables = self.metadata.list_all_entities(
            entity=Table,
            params={
                "database": self.config.source.serviceName + "." + database.name.__root__
            }
        )
        for table_entity in all_tables:
            yield table_entity

    def create_processor(self, service_connection_config):
        self.processor = get_processor(
            processor_type=self.config.processor.type,  # eject-metadata
            metadata_config=self.metadata_config,
            _from="eject",
            # Pass the session as kwargs for the profiler
            session=create_and_bind_session(
                self.create_engine_for_session(service_connection_config)
            ),
        )

    def create_engine_for_session(self, service_connection_config):
        """Create SQLAlchemy engine to use with a session object"""
        engine = get_connection(service_connection_config)
        test_connection(engine)

        return engine

    def execute(self):
        """
        Create the trino connection and run the ejection back to trino
        """
        copy_service_connection_config = deepcopy(
            self.config.source.serviceConnection.__root__.config
        )
        session = self.create_engine_for_session(copy_service_connection_config)

        # create theprocessor
        self.processor = EjectProcessor.create(session)

        # configure the processor
        for database in self.get_database_entities():
            for table_entity in self.get_table_entities(database):
                self.processor.process(table_entity) # pass in the table_entity
        r = 1
