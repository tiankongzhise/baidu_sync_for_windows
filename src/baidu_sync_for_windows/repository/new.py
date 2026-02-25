"""
MysqlRepository 的优化实现：通过类型别名 + 配置表替代重复分支，同时满足 basedpyright 类型检查。
"""
from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Tuple,
    Type,
    TypeGuard,
    Union,
    cast,
    overload,
)
from dataclasses import dataclass

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
    OauthRecord,
    SourceObjectRecord,
    ObjectHashRecord,
    ObjectCompressRecord,
    ObjectVerifyRecord,
    ObjectBackupRecord,
    ObjectEncryptNameCompressRecord,
    ObjectEncryptNameVerifyRecord,
    ObjectEncryptNameBackupRecord,
)
from baidu_sync_for_windows.exception import RepositoryException
from baidu_sync_for_windows.logger import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

# ====================== 1. 类型别名（不用 TypeVar，避免“类型变量在此上下文中没有意义”） ======================

# 所有可保存的 DTO 实例类型
SaveableDTO = Union[
    ScanDTO, CompressDTO, VerifyDTO, BackupDTO, HashDTO,
]
# 所有 DTO 的类类型（用于 get(id, dto_type) 的键与字典）
DTOClass = Union[
    Type[ScanDTO], Type[CompressDTO], Type[VerifyDTO], Type[BackupDTO], Type[HashDTO],
    Type[EncryptNameCompressDTO], Type[EncryptNameVerifyDTO], Type[EncryptNameBackupDTO],
]
# 所有 Record 的联合类型
RecordUnion = Union[
    SourceObjectRecord, ObjectCompressRecord, ObjectVerifyRecord, ObjectBackupRecord,
    ObjectHashRecord, ObjectEncryptNameCompressRecord, ObjectEncryptNameVerifyRecord,
    ObjectEncryptNameBackupRecord,
]

# 保存处理器：接收 (self, dto) -> None
SaveHandler = Callable[["MysqlRepository", SaveableDTO], None]
# 按 id+dto_type 查询处理器：接收 (self, id, dto_type) -> Optional[Record]
GetByIdHandler = Callable[["MysqlRepository", int, DTOClass], Optional[RecordUnion]]


@dataclass(frozen=True)
class DTOToRecordMap:
    """一条 DTO <-> Record 的映射配置（不含泛型，便于推导字典类型）。"""
    dto_cls: DTOClass
    record_cls: Type[RecordUnion]
    get_handler: GetByIdHandler
    save_handler: Optional[SaveHandler] = None


# 核心配置表：仅需维护此处
DTO_RECORD_MAPPINGS: Tuple[DTOToRecordMap, ...] = (
    DTOToRecordMap(
        dto_cls=ScanDTO,
        record_cls=SourceObjectRecord,
        get_handler=lambda self, id, dto: self._get_source_object_by_id(id, cast(Type[ScanDTO], dto)),
        save_handler=lambda self, data: self._save_scan_dto(cast(ScanDTO, data)),
    ),
    DTOToRecordMap(
        dto_cls=CompressDTO,
        record_cls=ObjectCompressRecord,
        get_handler=lambda self, id, dto: self._get_object_compress_record(id, cast(Type[CompressDTO], dto)),
        save_handler=lambda self, data: self._save_compress_dto(cast(CompressDTO, data)),
    ),
    DTOToRecordMap(
        dto_cls=VerifyDTO,
        record_cls=ObjectVerifyRecord,
        get_handler=lambda self, id, dto: self._get_object_verify_record(id, cast(Type[VerifyDTO], dto)),
        save_handler=lambda self, data: self._save_verify_dto(cast(VerifyDTO, data)),
    ),
    DTOToRecordMap(
        dto_cls=BackupDTO,
        record_cls=ObjectBackupRecord,
        get_handler=lambda self, id, dto: self._get_object_backup_record(id, cast(Type[BackupDTO], dto)),
        save_handler=lambda self, data: self._save_backup_dto(cast(BackupDTO, data)),
    ),
    DTOToRecordMap(
        dto_cls=HashDTO,
        record_cls=ObjectHashRecord,
        get_handler=lambda self, id, dto: self._get_object_hash_record(id, cast(Type[HashDTO], dto)),
        save_handler=lambda self, data: self._save_hash_dto(cast(HashDTO, data)),
    ),
    DTOToRecordMap(
        dto_cls=EncryptNameCompressDTO,
        record_cls=ObjectEncryptNameCompressRecord,
        get_handler=lambda self, id, dto: self._get_object_encrypt_name_compress_record(id, cast(Type[EncryptNameCompressDTO], dto)),
    ),
    DTOToRecordMap(
        dto_cls=EncryptNameVerifyDTO,
        record_cls=ObjectEncryptNameVerifyRecord,
        get_handler=lambda self, id, dto: self._get_object_encrypt_name_verify_record(id, cast(Type[EncryptNameVerifyDTO], dto)),
    ),
    DTOToRecordMap(
        dto_cls=EncryptNameBackupDTO,
        record_cls=ObjectEncryptNameBackupRecord,
        get_handler=lambda self, id, dto: self._get_object_encrypt_name_backup_record(id, cast(Type[EncryptNameBackupDTO], dto)),
    ),
)

# 由配置表派生的查找表（类型为具体 Union，不再使用 TypeVar）
_SAVE_HANDLERS: Dict[DTOClass, SaveHandler] = {
    m.dto_cls: m.save_handler for m in DTO_RECORD_MAPPINGS if m.save_handler is not None
}
_GET_BY_ID_HANDLERS: Dict[DTOClass, GetByIdHandler] = {
    m.dto_cls: m.get_handler for m in DTO_RECORD_MAPPINGS
}


def _is_dto_class(obj: Any, dto_cls: DTOClass) -> TypeGuard[DTOClass]:
    """类型守卫：判断是否为某 DTO 类（可用于 isinstance 等）。"""
    return obj is dto_cls or (isinstance(obj, type) and issubclass(obj, dto_cls))


# ====================== 2. Repository 类 ======================


class MysqlRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.logger = get_logger(bind={"repository_name": "mysql"})
        self._test_connection()

    # ---------- save：保留重载，实现用配置表分发 ----------
    @overload
    def save(self, data: ScanDTO) -> None: ...
    @overload
    def save(self, data: CompressDTO) -> None: ...
    @overload
    def save(self, data: VerifyDTO) -> None: ...
    @overload
    def save(self, data: BackupDTO) -> None: ...
    @overload
    def save(self, data: HashDTO) -> None: ...

    def save(self, data: SaveableDTO) -> None:
        dto_type = type(data)
        handler = _SAVE_HANDLERS.get(dto_type)
        if not handler:
            raise RepositoryException(f"Unsupported data type for save: {dto_type.__name__}")
        try:
            handler(self, data)
        except Exception as e:
            self.logger.error("Failed to save %s: %s", dto_type.__name__, str(e))
            raise RepositoryException(f"Save failed for {dto_type.__name__}: {str(e)}") from e

    # ---------- get：重载保持调用处类型推断；实现用统一参数名以通过类型检查 ----------
    @overload
    def get(self, platform: str) -> Optional[OauthRecord]: ...
    @overload
    def get(self, drive_letter: str, target_object_path: str) -> Optional[SourceObjectRecord]: ...
    @overload
    def get(self, id: int, dto_type: Type[ScanDTO]) -> Optional[SourceObjectRecord]: ...
    @overload
    def get(self, id: int, dto_type: Type[CompressDTO]) -> Optional[ObjectCompressRecord]: ...
    @overload
    def get(self, id: int, dto_type: Type[VerifyDTO]) -> Optional[ObjectVerifyRecord]: ...
    @overload
    def get(self, id: int, dto_type: Type[BackupDTO]) -> Optional[ObjectBackupRecord]: ...
    @overload
    def get(self, id: int, dto_type: Type[HashDTO]) -> Optional[ObjectHashRecord]: ...
    @overload
    def get(self, id: int, dto_type: Type[EncryptNameCompressDTO]) -> Optional[ObjectEncryptNameCompressRecord]: ...
    @overload
    def get(self, id: int, dto_type: Type[EncryptNameVerifyDTO]) -> Optional[ObjectEncryptNameVerifyRecord]: ...
    @overload
    def get(self, id: int, dto_type: Type[EncryptNameBackupDTO]) -> Optional[ObjectEncryptNameBackupRecord]: ...

    def get(  # type: ignore[reportInconsistentOverload]
        self,
        platform: str | int,
        drive_letter_or_dto_type: str | DTOClass | None = None,
    ) -> Optional[Union[OauthRecord, RecordUnion]]:
        # 场景1: 仅传 platform (str)
        if drive_letter_or_dto_type is None and isinstance(platform, str):
            return self._get_oauth_record(platform)
        # 场景2: 两个 str -> SourceObjectRecord
        if isinstance(platform, str) and isinstance(drive_letter_or_dto_type, str):
            return self._get_source_object_record(platform, drive_letter_or_dto_type)
        # 场景3: id (int) + dto_type (类)
        if isinstance(platform, int) and isinstance(drive_letter_or_dto_type, type):
            dto_cls = drive_letter_or_dto_type
            if dto_cls in _GET_BY_ID_HANDLERS:
                return _GET_BY_ID_HANDLERS[dto_cls](self, platform, dto_cls)
        raise RepositoryException(
            f"Unsupported arguments for get: platform={type(platform).__name__}, "
            f"second={type(drive_letter_or_dto_type).__name__ if drive_letter_or_dto_type else 'None'}"
        )

    def _test_connection(self) -> None:
        try:
            with Session(self.engine) as session:
                session.execute(text("SELECT 1"))
                session.commit()
                self.logger.info("Connection test successful")
        except Exception as e:
            self.logger.error("Failed to test connection: %s", str(e))
            raise RepositoryException(f"Failed to test connection: {str(e)}") from e

    def update(self, id: str, data: SaveableDTO) -> None: ...
    def insert(self, data: SaveableDTO) -> None: ...
    def execute(self, query: str) -> None: ...

    def _save_scan_dto(self, data: ScanDTO) -> None: ...
    def _save_compress_dto(self, data: CompressDTO) -> None: ...
    def _save_verify_dto(self, data: VerifyDTO) -> None: ...
    def _save_backup_dto(self, data: BackupDTO) -> None: ...
    def _save_hash_dto(self, data: HashDTO) -> None: ...

    def _get_oauth_record(self, platform: str) -> Optional[OauthRecord]: ...
    def _get_source_object_record(self, drive_letter: str, target_object_path: str) -> Optional[SourceObjectRecord]: ...
    def _get_source_object_by_id(self, id: int, dto_type: Type[ScanDTO]) -> Optional[SourceObjectRecord]: ...
    def _get_object_hash_record(self, id: int, dto_type: Type[HashDTO]) -> Optional[ObjectHashRecord]: ...
    def _get_object_compress_record(self, id: int, dto_type: Type[CompressDTO]) -> Optional[ObjectCompressRecord]: ...
    def _get_object_verify_record(self, id: int, dto_type: Type[VerifyDTO]) -> Optional[ObjectVerifyRecord]: ...
    def _get_object_backup_record(self, id: int, dto_type: Type[BackupDTO]) -> Optional[ObjectBackupRecord]: ...
    def _get_object_encrypt_name_compress_record(
        self, id: int, dto_type: Type[EncryptNameCompressDTO]
    ) -> Optional[ObjectEncryptNameCompressRecord]: ...
    def _get_object_encrypt_name_verify_record(
        self, id: int, dto_type: Type[EncryptNameVerifyDTO]
    ) -> Optional[ObjectEncryptNameVerifyRecord]: ...
    def _get_object_encrypt_name_backup_record(
        self, id: int, dto_type: Type[EncryptNameBackupDTO]
    ) -> Optional[ObjectEncryptNameBackupRecord]: ...
