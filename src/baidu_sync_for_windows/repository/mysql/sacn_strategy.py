from typing import Any, Sequence
from sqlalchemy.orm import Session
from baidu_sync_for_windows.dtos import ScanDTO
from baidu_sync_for_windows.models import SourceObjectRecord
from baidu_sync_for_windows.logger import get_logger
from .base import RepositoryStrategyInterface


class Scanstrategy(RepositoryStrategyInterface[ScanDTO, SourceObjectRecord]):
    def __init__(self) -> None:
        super().__init__(SourceObjectRecord, ScanDTO)
        self.logger = get_logger(bind={"module_name":self.__class__.__name__})

    def insert(self, repo: Any, data: ScanDTO) -> SourceObjectRecord:
        record = super().insert(repo, data)
        self.logger.log("MODULE_INFO",f"scan strategy insert data: {data.model_dump()}")
        return record

    def update(self, repo: Any, data: ScanDTO) -> SourceObjectRecord:
        record = self._save_without_id(repo, data)
        self.logger.log("MODULE_INFO",f"scan strategy update data: {data.model_dump()}")
        return record

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
                self.logger.log("MODULE_INFO",f"scan strategy get by id: {id} not found")
                return None
            self.logger.log("MODULE_INFO",f"scan strategy get by id: {id} found")
            session.expunge(record)
            return record

    def get_by_source_object_id(
        self, repo: Any, source_object_id: int
    ) -> SourceObjectRecord | None:
        record = self.get_by_id(repo, source_object_id)
        if not record:
            self.logger.log("MODULE_INFO",f"scan strategy get by source object id: {source_object_id} not found")
            return None
        self.logger.log("MODULE_INFO",f"scan strategy get by source object id: {source_object_id} found")
        return record

    def save(self, repo: Any, data: ScanDTO) -> SourceObjectRecord:
        record = self._save_without_id(repo, data)
        self.logger.log("MODULE_INFO",f"scan strategy save data: {data.model_dump()}")
        return record

    def execute(self, repo: Any, query: str) -> Sequence[Any] | None:
        result = super().execute(repo, query)
        self.logger.log("MODULE_INFO",f"scan strategy execute query: {query} result: {result}")
        return result

    def is_equal(self, record: SourceObjectRecord, data: ScanDTO) -> bool:
        result = super().is_equal(record, data)
        self.logger.log("MODULE_INFO",f"scan strategy is equal: {result}")
        return result

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
                record = self.insert(repo, data)
                self.logger.log("MODULE_INFO",f"scan strategy _save_without_id: insert data: {data.model_dump()}")
                return record
            if self.is_equal(record, data):
                self.logger.log("MODULE_INFO",f"scan strategy _save_without_id: record is equal to data: {data.model_dump()}")
                return record
            self.logger.log("MODULE_INFO",f"scan strategy _save_without_id: update data: {data.model_dump()}")
            for key, value in data.model_dump().items():
                setattr(record, key, value)
            session.merge(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            self.logger.log("MODULE_INFO",f"scan strategy _save_without_id: update data: {data.model_dump()}")
            return record
