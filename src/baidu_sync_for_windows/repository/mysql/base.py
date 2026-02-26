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
        self.logger = get_logger(bind={"module_name":self.__class__.__name__})
    @abstractmethod
    def insert(self, repo, data: DTO) -> Record:
        with Session(repo.engine) as session:
            record = self.record_class(**data.model_dump())
            session.add(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            self.logger.log("MODULE_BASE_INFO",f"insert data: {data.model_dump()}")
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
            self.logger.log("MODULE_BASE_INFO",f"update data: {data.model_dump()}")
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
                self.logger.log("MODULE_BASE_INFO",f"get by source object id: {source_object_id}")
                return cast(Record, record)
            self.logger.log("MODULE_BASE_INFO",f"get by source object id: {source_object_id} not found")
            return None

    @abstractmethod
    def save(self, repo, data: DTO) -> Record:
        if getattr(data, "source_object_id", None) is None:
            self.logger.error(f"save failed: Source object id is required, data: {data}")
            raise RepositoryException(f"base strategy save failed: Source object id is required, data: {data}")
        record = self.get_by_source_object_id(repo, data.source_object_id)  # type: ignore
        if not record:
            self.logger.log("MODULE_BASE_INFO",f"save: insert data: {data.model_dump()}")
            return self.insert(repo, data)
        if self.is_equal(record, data):
            self.logger.log("MODULE_BASE_INFO",f"save: record is equal to data: {data.model_dump()}")
            return record
        self.logger.log("MODULE_BASE_INFO",f"save: update data: {data.model_dump()}")
        return self.update(repo, data)

    @abstractmethod
    def execute(self, repo, query: str) -> Sequence[Any] | None:
        with Session(repo.engine) as session:
            result = session.execute(text(query)).all()
            self.logger.log("MODULE_BASE_INFO",f"execute query: {query} result: {result}")
            return result
    @abstractmethod
    def is_equal(self, record: Record, data: DTO) -> bool:
        for key, value in data.model_dump().items():
            if getattr(record, key) != value:
                self.logger.debug(f"record:{record} is not equal dto:{data} key:{key} value:{getattr(record, key)} != {value}")
                return False
        self.logger.debug(f"record:{record} is equal to dto:{data}")
        return True
