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
from sqlalchemy import Engine
from typing import overload
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from typing import Type
from typing import cast

class MysqlRepository:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.logger = get_logger(bind={"repository_name": "mysql"})
        self._test_connection()

    @overload
    def save(self, data: ScanDTO): ...
    @overload
    def save(self, data: CompressDTO): ...
    @overload
    def save(self, data: VerifyDTO): ...
    @overload
    def save(self, data: BackupDTO): ...
    @overload
    def save(self, data: HashDTO): ...
    def save(self, data: ScanDTO | CompressDTO | VerifyDTO | BackupDTO | HashDTO):
        match data:
            case ScanDTO():
                self._save_scan_dto(data)
            case CompressDTO():
                self._save_compress_dto(data)
            case VerifyDTO():
                self._save_verify_dto(data)
            case BackupDTO():
                self._save_backup_dto(data)
            case HashDTO():
                self._save_hash_dto(data)
            case _:
                raise RepositoryException(f"Unsupported data type: {type(data)}")
    @overload
    def get(self,platform:str)->Optional[OauthRecord]: ...
    @overload
    def get(self,drive_letter:str,target_object_path:str)->Optional[SourceObjectRecord]: ...
    @overload
    def get(self,id:int,dto_type:Type[ScanDTO])->Optional[SourceObjectRecord]: ...
    @overload
    def get(self,id:int,dto_type:Type[CompressDTO])->Optional[ObjectCompressRecord]: ...
    @overload
    def get(self,id:int,dto_type:Type[VerifyDTO])->Optional[ObjectVerifyRecord]: ...
    @overload
    def get(self,id:int,dto_type:Type[BackupDTO])->Optional[ObjectBackupRecord]: ...
    @overload
    def get(self,id:int,dto_type:Type[HashDTO])->Optional[ObjectHashRecord]: ...
    @overload
    def get(self,id:int,dto_type:Type[EncryptNameCompressDTO])->Optional[ObjectEncryptNameCompressRecord]: ...
    @overload
    def get(self,id:int,dto_type:Type[EncryptNameVerifyDTO])->Optional[ObjectEncryptNameVerifyRecord]: ...
    @overload
    def get(self,id:int,dto_type:Type[EncryptNameBackupDTO])->Optional[ObjectEncryptNameBackupRecord]: ...
    def get(self, arg1: str | int, arg2: str | type[ScanDTO] | type[CompressDTO] | type[VerifyDTO] | type[BackupDTO] | type[HashDTO] | type[EncryptNameCompressDTO] | type[EncryptNameVerifyDTO] | type[EncryptNameBackupDTO] | None = None):  # type: ignore[InconsistentOverload]
        if arg2 is None:
            return self._get_oauth_record(cast(str, arg1))
        if isinstance(arg1, str) and isinstance(arg2, str):
            return self._get_source_object_record(arg1, arg2)
        if isinstance(arg1, int):
            if arg2 is ScanDTO:
                return self._get_source_object_by_id(arg1, arg2)
            if arg2 is CompressDTO:
                return self._get_object_compress_record(arg1, arg2)
            if arg2 is VerifyDTO:
                return self._get_object_verify_record(arg1, arg2)
            if arg2 is BackupDTO:
                return self._get_object_backup_record(arg1, arg2)
            if arg2 is HashDTO:
                return self._get_object_hash_record(arg1, arg2)
            if arg2 is EncryptNameCompressDTO:
                return self._get_object_encrypt_name_compress_record(arg1, arg2)
            if arg2 is EncryptNameVerifyDTO:
                return self._get_object_encrypt_name_verify_record(arg1, arg2)
            if arg2 is EncryptNameBackupDTO:
                return self._get_object_encrypt_name_backup_record(arg1, arg2)
        raise RepositoryException(f"Unsupported argument types: {type(arg1)}, {type(arg2)}")

    def _get_oauth_record(self,platform:str)->Optional[OauthRecord]:
        ...
    def _get_source_object_record(self,drive_letter:str,target_object_path:str)->Optional[SourceObjectRecord]:
        ...
    def _get_source_object_by_id(self,id:int,dto_type:Type[ScanDTO])->Optional[SourceObjectRecord]:
        ...
    def _get_object_hash_record(self,id:int,dto_type:Type[HashDTO])->Optional[ObjectHashRecord]:
        ...
    def _get_object_compress_record(self,id:int,dto_type:Type[CompressDTO])->Optional[ObjectCompressRecord]:
        ...
    def _get_object_verify_record(self,id:int,dto_type:Type[VerifyDTO])->Optional[ObjectVerifyRecord]:
        ...
    def _get_object_backup_record(self,id:int,dto_type:Type[BackupDTO])->Optional[ObjectBackupRecord]:
        ...
    def _get_object_encrypt_name_compress_record(self,id:int,dto_type:Type[EncryptNameCompressDTO])->Optional[ObjectEncryptNameCompressRecord]:
        ...
    def _get_object_encrypt_name_verify_record(self,id:int,dto_type:Type[EncryptNameVerifyDTO])->Optional[ObjectEncryptNameVerifyRecord]:
        ...
    def _get_object_encrypt_name_backup_record(self,id:int,dto_type:Type[EncryptNameBackupDTO])->Optional[ObjectEncryptNameBackupRecord]:
        ...
    def update(self, id: str, data: ScanDTO | CompressDTO | VerifyDTO | BackupDTO): ...
    def insert(self, data: ScanDTO | CompressDTO | VerifyDTO | BackupDTO): ...
    def execute(self, query: str): ...
    def _test_connection(self):
        try:
            with Session(self.engine) as session:
                session.execute(text("SELECT 1"))
                session.commit()
                self.logger.info("Connection test successful")
        except Exception as e:
            self.logger.error(f"Failed to test connection: {e}")
            raise RepositoryException(f"Failed to test connection: {e}")

    def _save_scan_dto(self, data: ScanDTO): ...
    def _save_compress_dto(self, data: CompressDTO): ...
    def _save_verify_dto(self, data: VerifyDTO): ...
    def _save_backup_dto(self, data: BackupDTO): ...
    def _save_hash_dto(self, data: HashDTO): ...
