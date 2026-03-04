from typing import cast
from sqlalchemy.orm import Session
from baidu_sync_for_windows.dtos import ScanDTO
from baidu_sync_for_windows.models import SourceRecord
from baidu_sync_for_windows.logger import get_logger
from .base import RepositoryStrategyInterface


class ScanStrategy(
    RepositoryStrategyInterface[
        ScanDTO, SourceRecord, SourceRecord, SourceRecord
    ]
):
    def __init__(self) -> None:
        super().__init__(
            ScanDTO, SourceRecord, SourceRecord, SourceRecord
        )
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})
    def save(self, data: ScanDTO) -> SourceRecord:
        return self._save( data)
    def get_source_record_by_source_id(self, source_id: int) -> SourceRecord | None:
        return self._default_get_source_record_by_source_id( source_id)
    def get_latest_service_record_by_source_id(self, source_id: int) -> SourceRecord | None:
        return self._default_get_latest_service_record_by_source_id( source_id)
    def get_record_by_source_id(self, source_id: int) -> SourceRecord | None:
        return self._default_get_record_by_source_id( source_id)
    def is_processed(self, source_id: int) -> bool:
        return self._default_is_processed( self.source_record_class, self.record_class, source_id)
    def _save(self,data: ScanDTO) -> SourceRecord:
        record = self._get_record_by_unique_column(data)
        if record:
            return self._default_update(    record, data)
        return self._default_insert( data)
    
    def _get_record_by_unique_column(self, data: ScanDTO) -> SourceRecord | None:
        with Session(self.engine) as session:
            record = session.query(self.record_class).filter(getattr(self.record_class, "computer_unique_tag") == data.computer_unique_tag, getattr(self.record_class, "target_object_path") == data.target_object_path).first()
            if record:
                return cast(SourceRecord, record)
            return None


if __name__ == "__main__":
    strategy = ScanStrategy()
    print(strategy.dto_class)