from typing import cast
from sqlalchemy.orm import Session
from baidu_sync_for_windows.dtos import ScanDTO
from baidu_sync_for_windows.models import SourceRecord
from baidu_sync_for_windows.logger import get_logger
from .base import RepositoryStrategyInterface, RepositoryProtocol


class Scanstrategy(
    RepositoryStrategyInterface[
        ScanDTO, SourceRecord, SourceRecord, SourceRecord
    ]
):
    def __init__(self) -> None:
        super().__init__(
            ScanDTO, SourceRecord, SourceRecord, SourceRecord
        )
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})
    def save(self, repo: RepositoryProtocol, data: ScanDTO) -> SourceRecord:
        return self._save(repo, data)
    def get_source_record_by_source_id(self, repo: RepositoryProtocol, source_id: int) -> SourceRecord | None:
        self.logger.warning('scan repository has no source id,because source id is the key of source record, use id instead')
        return self._get_record_by_id(repo, source_id)
    def get_latest_service_record_by_source_id(self, repo: RepositoryProtocol, source_id: int) -> SourceRecord | None:
        self.logger.warning('scan repository has no latest service record, use scan record instead')
        return self._get_record_by_id(repo, source_id)
    def get_record_by_source_id(self, repo: RepositoryProtocol, source_id: int) -> SourceRecord | None:
        self.logger.warning('scan repository has no source id,because source id is the key of source record, use id instead')
        return self._get_record_by_id(repo, source_id)

    def _get_record_by_id(self, repo: RepositoryProtocol, id: int) -> SourceRecord | None:
        with Session(repo.engine) as session:
            record = session.query(self.record_class).filter(getattr(self.record_class, "id") == id).first()
            if record:
                return cast(SourceRecord, record)
            return None
    def _save(self, repo: RepositoryProtocol, data: ScanDTO) -> SourceRecord:
        record = self._get_record_by_unique_column(repo, data)
        if record:
            return self._default_update(repo, record, data)
        return self._default_insert(repo, data)
    
    def _get_record_by_unique_column(self, repo: RepositoryProtocol, data: ScanDTO) -> SourceRecord | None:
        with Session(repo.engine) as session:
            record = session.query(self.record_class).filter(getattr(self.record_class, "drive_letter") == data.drive_letter, getattr(self.record_class, "target_object_path") == data.target_object_path).first()
            if record:
                return cast(SourceRecord, record)
            return None


if __name__ == "__main__":
    strategy = Scanstrategy()
    print(strategy.dto_class)