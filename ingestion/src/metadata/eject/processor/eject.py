from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import select, text

from metadata.ingestion.api.processor import Processor, ProcessorStatus
from metadata.generated.schema.entity.data.table import Table

@dataclass
class EjectStatus(ProcessorStatus):
    # tests: List[str] = field(default_factory=list)

    # def tested(self, record: str, type) -> None:
    #     self.tests.append(record)
    #     # logger.info(f"Table tested: {record}")
    val = 1

class EjectProcessor(Processor[Table]):
    """
    For each table, eject the comment
    back to the service.
    """
    status: EjectStatus

    def __init__(
        self,
        session: Session
    ):
        super().__init__()
        self.status = EjectStatus()
        self.session = session

    @classmethod
    def create(
        cls,
        session: Session
    ):
        return cls(session)

    def process(self, table_entity: Table):
        description = table_entity.description
        table_path = table_entity.databaseSchema + "." + table_entity.name
        connection = self.session.connection()

        # eject the table metadata
        connection.execute(text("COMMENT ON TABLE {} is {}".format(table_path, description)))

        # eject the column metadata
        for col in table_entity.columns:
            column_path = table_path + "." + col.name
            description = col.description
            connection.execute(text("COMMENT ON TABLE {} is {}".format(column_path, description)))

