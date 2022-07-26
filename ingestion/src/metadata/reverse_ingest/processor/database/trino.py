
from metadata.reverse_ingest.processor.database.common_db_processor import CommonDbProcessor


class TrinoProcessor(CommonDbProcessor):
    """
    Supported Metadata: table and column description
    """

    def __init__(self, session, metadata, service_name):
        super().__init__(session, metadata, service_name)

    def supportsDatabaseComment(self):
        return False
