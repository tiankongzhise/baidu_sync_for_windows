from abc import ABC, abstractmethod
from typing_extensions import TypeAlias
from sqlalchemy.orm import Session
from sqlalchemy import Engine,TextClause,text
from typing import Generic, TypeVar, Any
from typing import Type, cast, Protocol
from baidu_sync_for_windows.exception import RepositoryException
from .default import create_default_engine
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
        engine: Engine|None = None,
    ):
        self.dto_class = dto_class
        self.record_class = record_class
        self.source_record_class = source_record_class
        self.last_service_record_class = last_service_record_class
        self.engine = engine or create_default_engine()
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})


    def _default_insert(self, data: DTO_T) -> Record_T:
        if type(data) is not self.dto_class:
            self.logger.error(
                f"DTO type mismatch: expected {self.dto_class.__name__}, got {type(data).__name__}. "
                "Wrong strategy may write to wrong table."
            )
            raise RepositoryException(
                f"DTO type mismatch: strategy is for {self.dto_class.__name__}, got {type(data).__name__}"
            )
        try:
            with Session(self.engine) as session:
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
    def _default_update(self, record: Record_T, data: DTO_T) -> Record_T:
        if self._default_is_equal(record, data):
            self.logger.log("MODULE_BASE_INFO", f"record: {record} is equal to data: {data}, no need to update")
            return record
        with Session(self.engine) as session:
            for key, value in data.model_dump().items():
                setattr(record, key, value)
            session.merge(record)
            session.commit()
            self.logger.log("MODULE_BASE_INFO", f"update data: {data.model_dump()}, record: {record}")
            return cast(Record_T, record)


    @abstractmethod
    def get_source_record_by_source_id(
        self, source_id: int
    ) -> SourceRecord_T | None: ...
    def _default_get_source_record_by_source_id(
        self, source_id: int
    ) -> SourceRecord_T | None:
        with Session(self.engine) as session:
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
        self, source_id: int
    ) -> LastServiceRecord_T | None: ...
    def _default_get_latest_service_record_by_source_id(
        self, source_id: int
    ) -> LastServiceRecord_T | None:
        with Session(self.engine) as session:
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
        self, source_id: int
    ) -> Record_T | None: ...
    def _default_get_record_by_source_id(
        self, source_id: int
    ) -> Record_T | None:
        with Session(self.engine) as session:
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
    def save(self, data: DTO_T) -> Record_T: ...
    def _default_save(self, data: DTO_T) -> Record_T:
        if getattr(data, "source_id", None) is None:
            self.logger.error(
                f"save failed: Source id is required, data: {data}"
            )
            raise RepositoryException(
                f"base strategy save failed: Source id is required, data: {data}"
            )
        record = self._default_get_record_by_source_id(getattr(data, "source_id"))  
        if not record:
            self.logger.log(
                "MODULE_BASE_INFO", f"save: insert data: {data.model_dump()}"
            )
            return self._default_insert( data)
        result = self._default_update( record,data)
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

    def _default_execute_sql(self, sql: TextClause, *args, **kwargs) -> Any:
        """执行原生 SQL，*args/**kwargs 会合并为绑定参数透传给 session.execute(statement, parameters)。"""
        params: dict[str, Any] = {}
        if len(args) == 1 and isinstance(args[0], dict):
            params = dict(args[0])
        params.update(kwargs)
        with Session(self.engine) as session:
            return session.execute(sql, params)
    @abstractmethod
    def is_processed(self, source_id: int) -> bool:...

    def _default_is_processed(self,source_record: RecordClass, process_record: RecordClass,source_id: int) -> bool:
        sql = self._get_default_is_processed_sql(source_record.__tablename__, process_record.__tablename__, "id", "source_id", source_id)
        result = self._default_execute_sql( text(sql))
        result = result.scalar()
        if result:
            return True
        return False
    def _get_default_is_processed_sql(self, source_record_name: str, process_record_name: str, source_record_col: str, process_record_col: str, unique_value: int) -> str:
        sql_temp = f'''SELECT 
            CASE
                -- 1. {process_record_name}不存在，直接返回false
                WHEN hr.{process_record_col} IS NULL THEN FALSE
                -- 2. {process_record_name}更新时间非空的情况
                WHEN hr.updated_at IS NOT NULL THEN
                    CASE
                        -- {source_record_name}更新时间非空，且大于{process_record_name}更新时间 → false
                        WHEN sr.updated_at IS NOT NULL AND sr.updated_at > hr.updated_at THEN FALSE
                        -- {source_record_name}更新时间为空，用创建时间比较，且大于{process_record_name}更新时间 → false
                        WHEN sr.updated_at IS NULL AND sr.created_at > hr.updated_at THEN FALSE
                        -- 不满足则返回true
                        ELSE TRUE
                    END
                -- 3. {process_record_name}更新时间为空的情况
                WHEN hr.updated_at IS NULL THEN
                    CASE
                        -- {source_record_name}更新时间非空，且大于{process_record_name}创建时间 → false
                        WHEN sr.updated_at IS NOT NULL AND sr.updated_at > hr.created_at THEN FALSE
                        -- {source_record_name}更新时间为空，用创建时间比较，且大于{process_record_name}创建时间 → false
                        WHEN sr.updated_at IS NULL AND sr.created_at > hr.created_at THEN FALSE
                        -- 不满足则返回true
                        ELSE TRUE
                    END
                -- 兜底返回true
                ELSE TRUE
            END AS result
        FROM 
            {source_record_name} sr
        LEFT JOIN 
            {process_record_name} hr ON sr.{source_record_col} = hr.{process_record_col}
        -- 替换为你要查询的具体source_id
        WHERE 
            sr.{source_record_col} = {unique_value};'''
        return sql_temp