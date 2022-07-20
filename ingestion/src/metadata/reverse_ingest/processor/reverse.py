"""

"""
from dataclasses import dataclass, field
from pickle import TRUE
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text
from sqlalchemy.exc import OperationalError

from metadata.ingestion.api.processor import Processor, ProcessorStatus
from metadata.generated.schema.entity.data.table import Table

from metadata.utils.logger import reverse_logger

logger = reverse_logger()

@dataclass
class ReverseStatus(ProcessorStatus):
    """
    Keep track of which metadata have been pushed to a database service
    """
    items: List[str] = field(default_factory=list)

    def table_status(self, record: str, type) -> None:
        self.items.append(record)
        logger.info(f"Table metadata pushed for: {record}")

    def column_status(self, record: str, type) -> None:
        self.items.append(record)
        logger.info(f"Column metadata pushed for: {record}")

class ReverseProcessor(Processor[Table]):
    """
    For each table, eject the comment
    back to the service.
    """
    status: ReverseStatus

    def __init__(
        self,
        session: Session
    ):
        super().__init__()
        self.status = ReverseStatus()
        self.session = session

    @classmethod
    def create(
        cls,
        session: Session
    ):
        return cls(session)

    def process(self, table_entity: Table):
        try:
            table_path = table_entity.databaseSchema.name + "." + table_entity.name.__root__
            if table_entity.description != None:
                description = table_entity.description.__root__

                # Update the table metadata
                self.session.execute(text("COMMENT ON TABLE {} is '{}'".format(table_path, description)))

                logger.info(f"Table description for table {table_entity.name.__root__} pushed to database")
            # Update the column metadata
            for col in table_entity.columns:

                column_path = table_path + "." + col.name.__root__

                if col.description != None:
                    description = col.description.__root__

                    # Update the column metadata
                    self.session.execute(text("COMMENT ON COLUMN {} is '{}'".format(column_path, description)))

                    logger.info(f"Column description for column {col.name.__root__} pushed to database")
        except OperationalError as err:
            logger.error(f"Could not push back all updates for metadata in table {table_entity.name.__root__}")

    def get_status(self) -> ProcessorStatus:
        return self.status

    def close(self) -> None:
        self.session.close()
