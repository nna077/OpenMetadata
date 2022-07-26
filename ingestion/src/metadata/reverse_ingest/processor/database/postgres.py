
from metadata.reverse_ingest.processor.database.common_db_processor import CommonDbProcessor


class PostgresProcessor(CommonDbProcessor):
    """
    Supported Metadata: database, table and column description
    """

    def __init__(self, session, metadata):
        super().__init__(session, metadata)
