
from baidu_sync_for_windows.dtos import HashDTO
from baidu_sync_for_windows.models import HashRecord,SourceRecord
from baidu_sync_for_windows.logger import get_logger
from .base import RepositoryStrategyInterface, RepositoryProtocol


class HashStrategy(
    RepositoryStrategyInterface[
        HashDTO, HashRecord, SourceRecord, SourceRecord
    ]
):
    """HashDTO 的仓储策略，对应 HashRecord / hash_record 表。"""

    def __init__(self) -> None:
        super().__init__(
            HashDTO, HashRecord, SourceRecord, SourceRecord
        )
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})
    def save(self, repo: RepositoryProtocol, data: HashDTO) -> HashRecord:
        return self._default_save(repo, data)
    def get_source_record_by_source_id(self, repo: RepositoryProtocol, source_id: int) -> SourceRecord | None:
        return self._default_get_source_record_by_source_id(repo, source_id)
    def get_latest_service_record_by_source_id(self, repo: RepositoryProtocol, source_id: int) -> SourceRecord | None:
        return self._default_get_latest_service_record_by_source_id(repo, source_id)
    def get_record_by_source_id(self, repo: RepositoryProtocol, source_id: int) -> HashRecord | None:
        return self._default_get_record_by_source_id(repo, source_id)