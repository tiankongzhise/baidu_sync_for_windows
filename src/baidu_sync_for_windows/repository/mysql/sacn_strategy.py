from typing import Any, Sequence
from sqlalchemy.orm import Session
from baidu_sync_for_windows.dtos import ScanDTO
from baidu_sync_for_windows.models import SourceObjectRecord
from .base import RepositoryStrategyInterface


class Scanstrategy(RepositoryStrategyInterface[ScanDTO, SourceObjectRecord]):
    def __init__(self) -> None:
        super().__init__(SourceObjectRecord, ScanDTO)

    def insert(self, repo: Any, data: ScanDTO) -> SourceObjectRecord:
        return super().insert(repo, data)

    def update(self, repo: Any, data: ScanDTO) -> SourceObjectRecord:
        return self._save_without_id(repo, data)

    def get_by_id(
        self, repo: Any, id: int
    ) -> SourceObjectRecord | None:
        with Session(repo.engine) as session:
            record = (
                session.query(SourceObjectRecord)
                .filter(SourceObjectRecord.id == id)
                .first()
            )
            if not record:
                return None
            session.expunge(record)
            return record

    def get_by_source_object_id(
        self, repo: Any, source_object_id: int
    ) -> SourceObjectRecord | None:
        return self.get_by_id(repo, source_object_id)

    def save(self, repo: Any, data: ScanDTO) -> SourceObjectRecord:
        return self._save_without_id(repo, data)

    def execute(self, repo: Any, query: str) -> Sequence[Any] | None:
        return super().execute(repo, query)

    def is_equal(self, record: SourceObjectRecord, data: ScanDTO) -> bool:
        return super().is_equal(record, data)

    def _save_without_id(
        self, repo: Any, data: ScanDTO
    ) -> SourceObjectRecord:
        with Session(repo.engine) as session:
            record = (
                session.query(SourceObjectRecord)
                .filter(
                    SourceObjectRecord.drive_letter == data.drive_letter,
                    SourceObjectRecord.target_object_path == data.target_object_path,
                )
                .first()
            )
            if not record:
                return self.insert(repo, data)
            if self.is_equal(record, data):
                return record
            for key, value in data.model_dump().items():
                setattr(record, key, value)
            session.merge(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record
