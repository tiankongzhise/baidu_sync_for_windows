from abc import ABC, abstractmethod
from typing_extensions import TypeAlias
from sqlalchemy.orm import Session
from sqlalchemy import Engine
from typing import Generic, TypeVar
from typing import Type, cast, Protocol
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
    SourceRecord,
    CompressRecord,
    VerifyRecord,
    BackupRecord,
    HashRecord,
    EncryptNameCompressRecord,
    EncryptNameVerifyRecord,
    EncryptNameBackupRecord,
)
from baidu_sync_for_windows.logger import get_logger

DTO: TypeAlias = (
    ScanDTO
    | CompressDTO
    | VerifyDTO
    | BackupDTO
    | HashDTO
    | EncryptNameCompressDTO
    | EncryptNameVerifyDTO
    | EncryptNameBackupDTO
)

Record: TypeAlias = (
    SourceRecord
    | CompressRecord
    | VerifyRecord
    | BackupRecord
    | HashRecord
    | EncryptNameCompressRecord
    | EncryptNameVerifyRecord
    | EncryptNameBackupRecord
)

DTOClass: TypeAlias = Type[DTO]
RecordClass: TypeAlias = Type[Record]

# 泛型形参：子类可指定具体的 DTO / Record，使重写方法类型兼容
DTO_T = TypeVar("DTO_T", bound=DTO)
Record_T = TypeVar("Record_T", bound=Record)
SourceRecord_T = TypeVar("SourceRecord_T", bound=Record)
LastServiceRecord_T = TypeVar("LastServiceRecord_T", bound=Record)


class RepositoryProtocol(Protocol):
    engine: Engine


class RepositoryStrategyInterface(
    ABC, Generic[DTO_T, Record_T, SourceRecord_T, LastServiceRecord_T]
):
    """策略接口。子类继承时指定 Generic 参数可获得具体 DTO/Record 类型，重写方法类型兼容。"""

    def __init__(
        self,
        dto_class: Type[DTO_T],
        record_class: Type[Record_T],
        source_record_class: Type[SourceRecord_T],
        last_service_record_class: Type[LastServiceRecord_T],
    ):
        self.dto_class = dto_class
        self.record_class = record_class
        self.source_record_class = source_record_class
        self.last_service_record_class = last_service_record_class
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})


    def _default_insert(self, repo: RepositoryProtocol, data: DTO_T) -> Record_T:
        if type(data) is not self.dto_class:
            self.logger.error(
                f"DTO type mismatch: expected {self.dto_class.__name__}, got {type(data).__name__}. "
                "Wrong strategy may write to wrong table."
            )
            raise RepositoryException(
                f"DTO type mismatch: strategy is for {self.dto_class.__name__}, got {type(data).__name__}"
            )
        try:
            with Session(repo.engine) as session:
                record = self.record_class(**data.model_dump())
                session.add(record)
                session.commit()
                session.refresh(record)
                session.expunge(record)
                self.logger.log("MODULE_BASE_INFO", f"insert data: {data.model_dump()}, record: {record}")
                return cast(Record_T, record)
        except Exception as e:
            self.logger.exception(
                f"insert failed for {self.record_class.__name__}, data={data.model_dump()}: {e}"
            )
            raise RepositoryException(
                f"insert failed for {self.record_class.__name__}: {e}"
            ) from e
    def _default_update(self, repo: RepositoryProtocol, record: Record_T, data: DTO_T) -> Record_T:
        if self._default_is_equal(record, data):
            self.logger.log("MODULE_BASE_INFO", f"record: {record} is equal to data: {data}, no need to update")
            return record
        with Session(repo.engine) as session:
            for key, value in data.model_dump().items():
                setattr(record, key, value)
            session.merge(record)
            session.commit()
            self.logger.log("MODULE_BASE_INFO", f"update data: {data.model_dump()}, record: {record}")
            return cast(Record_T, record)


    @abstractmethod
    def get_source_record_by_source_id(
        self, repo: RepositoryProtocol, source_id: int
    ) -> SourceRecord_T | None: ...
    def _default_get_source_record_by_source_id(
        self, repo: RepositoryProtocol, source_id: int
    ) -> SourceRecord_T | None:
        with Session(repo.engine) as session:
            record = (
                session.query(self.source_record_class)
                .filter(getattr(self.source_record_class, "id") == source_id)
                .first()
            )
            if record:
                self.logger.log(
                    "MODULE_BASE_INFO",
                    f"get source object record by id: {source_id}",
                )
                return cast(SourceRecord_T, record)
            self.logger.log(
                "MODULE_BASE_INFO",
                f"get source object record by id: {source_id} not found",
            )
            return None

    @abstractmethod
    def get_latest_service_record_by_source_id(
        self, repo: RepositoryProtocol, source_id: int
    ) -> LastServiceRecord_T | None: ...
    def _default_get_latest_service_record_by_source_id(
        self, repo: RepositoryProtocol, source_id: int
    ) -> LastServiceRecord_T | None:
        with Session(repo.engine) as session:
            record = (
                session.query(self.last_service_record_class)
                .filter(
                    getattr(self.last_service_record_class, "source_id")
                    == source_id
                )
                .first()
            )
            if record:
                self.logger.log(
                    "MODULE_BASE_INFO",
                    f"get last service record by id: {source_id}",
                )
                return cast(LastServiceRecord_T, record)
            self.logger.log(
                "MODULE_BASE_INFO",
                f"get last service record by id: {source_id} not found",
            )
            return None
    @abstractmethod
    def get_record_by_source_id(
        self, repo: RepositoryProtocol, source_id: int
    ) -> Record_T | None: ...
    def _default_get_record_by_source_id(
        self, repo: RepositoryProtocol, source_id: int
    ) -> Record_T | None:
        with Session(repo.engine) as session:
            record = (
                session.query(self.record_class)
                .filter(
                    getattr(self.record_class, "source_id") == source_id
                )
                .first()
            )
            if record:
                self.logger.log(
                    "MODULE_BASE_INFO",
                    f"get record by source id: {source_id}",
                )
                return cast(Record_T, record)
            self.logger.log(
                "MODULE_BASE_INFO",
                f"get record by source id: {source_id} not found",
            )
            return None

    @abstractmethod
    def save(self, repo: RepositoryProtocol, data: DTO_T) -> Record_T: ...
    def _default_save(self, repo: RepositoryProtocol, data: DTO_T) -> Record_T:
        if getattr(data, "source_id", None) is None:
            self.logger.error(
                f"save failed: Source id is required, data: {data}"
            )
            raise RepositoryException(
                f"base strategy save failed: Source id is required, data: {data}"
            )
        record = self._default_get_record_by_source_id(repo,getattr(data, "source_id"))  
        if not record:
            self.logger.log(
                "MODULE_BASE_INFO", f"save: insert data: {data.model_dump()}"
            )
            return self._default_insert(repo, data)
        result = self._default_update(repo, record,data)
        self.logger.log("MODULE_BASE_INFO", f"save: update data: {data.model_dump()}")
        return result



    def _default_is_equal(self, record: Record_T, data: DTO_T) -> bool:
        for key, value in data.model_dump().items():
            if getattr(record, key) != value:
                self.logger.debug(
                    f"record:{record} is not equal dto:{data} key:{key} value:{getattr(record, key)} != {value}"
                )
                return False
        self.logger.debug(f"record:{record} is equal to dto:{data}")
        return True
