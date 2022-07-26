"""
Generic class to push metadata back to database services
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.ingestion.source.database.database_service import SQLSourceStatus
from metadata.generated.schema.entity.data.database import Database
from metadata.generated.schema.entity.data.table import Column, Table
from metadata.reverse_ingest.processor.database.database_processor import DatabaseProcessor
from metadata.ingestion.api.processor import Processor, ProcessorStatus
from metadata.utils.logger import reverse_logger

logger = reverse_logger()

class CommonDbProcessor(DatabaseProcessor, Processor):

    def __init__(self, session: Session, metadata: OpenMetadata, service_name: str):
        """
        Initalize the details to be pushed back to the database
        """
        self.session = session
        self.metadata = metadata
        self.service_name = service_name

    @classmethod
    def create(cls, session : Session, metadata : OpenMetadata, service_name : str):
        return cls(session, metadata, service_name)

    def set_database_comment(self, db: Database):
        if not self.supportsDatabaseComment() or db.description == None:
            logger.info("")
        else:
            try:
                db_name = db.name.__root__
                comment = db.description.__root__
                query = "COMMENT ON Database {} is '{}'".format(db_name, comment)
                self.session.execute(text(query))
                # logger needed
            except SQLAlchemyError:
                pass
                # logger needed

    def set_table_comment(self, table : Table, path : str):

        if not self.supportsTableComment() or table.description == None:
            print(1)
        else:
            try:
                comment = table.description.__root__
                query = "COMMENT ON TABLE {} is '{}'".format(path, comment)
                self.session.execute(text(query))
                # logger needed
            except SQLAlchemyError:
                pass
                # logger needed

    def set_column_comment(self, col : Column, path : str):

        if not self.supportsColumnComment() or col.description == None:
            print(2)
        else:
            try:
                comment = col.description.__root__
                query = "COMMENT ON COLUMN {} is '{}'".format(path, comment)
                self.session.execute(text(query))
                # logger needed
            except SQLAlchemyError:
                pass
                # logger needed

    def get_database_entities(self):
        """List all databases in service"""

        for database in self.metadata.list_all_entities(
            entity=Database,
            params={"service": self.service_name},
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
                "database": self.service_name + "." + database.name.__root__
            }
        )
        for table_entity in all_tables:
            yield table_entity

    def process(self):
            try:
                db : Database
                for db in self.get_database_entities():
                    self.set_database_comment(db)

                    table : Table
                    for table in self.get_table_entities(db):
                        table_path = table.databaseSchema.name + "." + table.name.__root__
                        self.set_table_comment(table, table_path)

                        for col in table.columns:
                            col_path = table_path + "." + col.name.__root__
                            self.set_column_comment(col, col_path)

            except SQLAlchemyError:
                print(4)
                a = 1

    def get_status(self) -> "ProcessorStatus":
        pass

    def close(self) -> None:
        self.session.close()

    # get changed entities:

