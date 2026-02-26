from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import TypeVar, Any, Sequence, Generic
from typing import Type, cast
from baidu_sync_for_windows.exception import RepositoryException
from baidu_sync_for_windows.dtos import (
    ScanDTO,
    CompressDTO,
    VerifyDTO,
    BackupDTO,
    HashDTO,
    EncryptNameCompressDTO,
    EncryptNameVerifyDTO,
    EncryptNameBackupDTO,
)
from baidu_sync_for_windows.models import (
    SourceObjectRecord,
    ObjectCompressRecord,
    ObjectVerifyRecord,
    ObjectBackupRecord,
    ObjectHashRecord,
    ObjectEncryptNameCompressRecord,
    ObjectEncryptNameVerifyRecord,
    ObjectEncryptNameBackupRecord,
)
from baidu_sync_for_windows.logger import get_logger
DTO = TypeVar(
    "DTO",
    bound=ScanDTO
    | CompressDTO
    | VerifyDTO
    | BackupDTO
    | HashDTO
    | EncryptNameCompressDTO
    | EncryptNameVerifyDTO
    | EncryptNameBackupDTO,
)
Record = TypeVar(
    "Record",
    bound=SourceObjectRecord
    | ObjectCompressRecord
    | ObjectVerifyRecord
    | ObjectBackupRecord
    | ObjectHashRecord
    | ObjectEncryptNameCompressRecord
    | ObjectEncryptNameVerifyRecord
    | ObjectEncryptNameBackupRecord,
)


class RepositoryStrategyInterface(ABC, Generic[DTO, Record]):
    def __init__(self, record_class: Type[Record], dto_class: Type[DTO]):
        self.record_class = record_class
        self.dto_class = dto_class
    @abstractmethod
    def insert(self, repo, data: DTO) -> Record:
        with Session(repo.engine) as session:
            record = self.record_class(**data.model_dump())
            session.add(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return cast(Record, record)

    @abstractmethod
    def update(self, repo, data: DTO) -> Record:
        with Session(repo.engine) as session:
            record = self.get_by_source_object_id(repo, data.source_object_id)  # type: ignore
            for key, value in data.model_dump().items():
                if key == "source_object_id":
                    continue
                setattr(record, key, value)
            session.merge(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return cast(Record, record)

    @abstractmethod
    def get_by_source_object_id(self, repo, source_object_id) -> Record | None:
        with Session(repo.engine) as session:
            record = (
                session.query(self.record_class)
                .filter(
                    getattr(self.record_class, "source_object_id") == source_object_id
                )
                .first()
            )
            if record:
                return cast(Record, record)
            return None

    @abstractmethod
    def save(self, repo, data: DTO) -> Record:
        if getattr(data, "source_object_id", None) is None:
            raise RepositoryException(f"base strategy save failed: Source object id is required, data: {data}")
        record = self.get_by_source_object_id(repo, data.source_object_id)  # type: ignore
        if not record:
            return self.insert(repo, data)
        if self.is_equal(record, data):
            return record
        return self.update(repo, data)

    @abstractmethod
    def execute(self, repo, query: str) -> Sequence[Any] | None:
        with Session(repo.engine) as session:
            return session.execute(text(query)).all()
    @abstractmethod
    def is_equal(self, record: Record, data: DTO) -> bool:
        for key, value in data.model_dump().items():
            if getattr(record, key) != value:
                return False
        return True
