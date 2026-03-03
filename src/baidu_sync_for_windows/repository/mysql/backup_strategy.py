from baidu_sync_for_windows.dtos import BackupDTO
from baidu_sync_for_windows.models import BackupRecord,SourceRecord,VerifyRecord
from baidu_sync_for_windows.logger import get_logger
from .base import RepositoryStrategyInterface


class BackupStrategy(
    RepositoryStrategyInterface[
        BackupDTO, BackupRecord, SourceRecord, VerifyRecord
    ]
):
    """BackupDTO 的仓储策略，对应 BackupRecord / backup_record 表。"""

    def __init__(self) -> None:
        super().__init__(
            BackupDTO, BackupRecord, SourceRecord, VerifyRecord
        )
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})
    def save(self, data: BackupDTO) -> BackupRecord:
        return self._default_save( data)
    def get_source_record_by_source_id(self, source_id: int) -> SourceRecord | None:
        return self._default_get_source_record_by_source_id( source_id)
    def get_latest_service_record_by_source_id(self, source_id: int) -> VerifyRecord | None:
        return self._default_get_latest_service_record_by_source_id( source_id)
    def get_record_by_source_id(self, source_id: int) -> BackupRecord | None:
        return self._default_get_record_by_source_id( source_id)
    def is_processed(self, source_id: int) -> bool:
        return self._default_is_processed( self.source_record_class, self.record_class, source_id)