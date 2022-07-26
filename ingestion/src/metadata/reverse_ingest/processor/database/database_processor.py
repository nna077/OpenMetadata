"""
Base Class To Push Metadata back to Database Services
"""

from abc import abstractmethod, ABC
from sqlalchemy.orm import Session

from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.ingestion.source.database.database_service import SQLSourceStatus

class DatabaseProcessor(ABC):

    # status: SQLSourceStatus
    metadata: OpenMetadata
    session: Session

    def __init__(self) -> None:
        pass

    @abstractmethod
    def set_database_comment(self, db_path : str, comment : str):
        pass

    @abstractmethod
    def set_table_comment(self, table_path : str, comment : str):
        pass

    @abstractmethod
    def set_column_comment(self, column_path : str, comment : str):
        pass

    def supportsDatabaseComment(self):
        return True

    def supportsTableComment(self):
        return True

    def supportsColumnComment(self):
        return True


