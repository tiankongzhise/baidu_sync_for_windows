from baidu_sync_for_windows.dtos import VerifyDTO
from baidu_sync_for_windows.models import VerifyRecord,SourceRecord,CompressRecord
from baidu_sync_for_windows.logger import get_logger
from .base import RepositoryStrategyInterface, RepositoryProtocol


class VerifyStrategy(
    RepositoryStrategyInterface[
        VerifyDTO, VerifyRecord, SourceRecord, CompressRecord
    ]
):
    """VerifyDTO 的仓储策略，对应 VerifyRecord / verify_record 表。"""

    def __init__(self) -> None:
        super().__init__(
            VerifyDTO, VerifyRecord, SourceRecord, CompressRecord
        )
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})
    def save(self, repo: RepositoryProtocol, data: VerifyDTO) -> VerifyRecord:
        return self._default_save(repo, data)
    def get_source_record_by_source_id(self, repo: RepositoryProtocol, source_id: int) -> SourceRecord | None:
        return self._default_get_source_record_by_source_id(repo, source_id)
    def get_latest_service_record_by_source_id(self, repo: RepositoryProtocol, source_id: int) -> CompressRecord | None:
        return self._default_get_latest_service_record_by_source_id(repo, source_id)
    def get_record_by_source_id(self, repo: RepositoryProtocol, source_id: int) -> VerifyRecord | None:
        return self._default_get_record_by_source_id(repo, source_id)
    def is_processed(self, repo: RepositoryProtocol, source_id: int) -> bool:
        return self._default_is_processed(repo, self.source_record_class, self.record_class, source_id)