from .sacn_strategy import ScanStrategy
from .hash_strategy import HashStrategy
from .compress_strategy import CompressStrategy
from .verify_strategy import VerifyStrategy
from .backup_strategy import BackupStrategy
# from .encrypt_name_compress_strategy import EncryptNameCompressStrategy
# from .encrypt_name_verify_strategy import EncryptNameVerifyStrategy
# from .encrypt_name_backup_strategy import EncryptNameBackupStrategy

from .oauth_repository import OauthRepository

from baidu_sync_for_windows.dtos import (
    ScanDTO,
    HashDTO,
    CompressDTO,
    VerifyDTO,
    BackupDTO,
    EncryptNameCompressDTO,
    EncryptNameVerifyDTO,
    EncryptNameBackupDTO,
    OauthDTO,
)
from typing import Type, TypeAlias, overload, Literal
from baidu_sync_for_windows.exception import RepositoryException

DTOClass: TypeAlias = Type[
    ScanDTO
    | HashDTO
    | CompressDTO
    | VerifyDTO
    | BackupDTO
    | EncryptNameCompressDTO
    | EncryptNameVerifyDTO
    | EncryptNameBackupDTO
    | OauthDTO
]
StrategyClass: TypeAlias = Type[
    ScanStrategy | HashStrategy | CompressStrategy | VerifyStrategy | BackupStrategy | OauthRepository
]
StrategyInstance: TypeAlias = (
    ScanStrategy | HashStrategy | CompressStrategy | VerifyStrategy | BackupStrategy | OauthRepository
)


def get_repository_tag_map() -> dict[str | DTOClass, StrategyClass]:
    repository_tag_map = {
        "oauth": OauthRepository,
        OauthDTO: OauthRepository,
        "scan": ScanStrategy,
        ScanDTO: ScanStrategy,
        "hash": HashStrategy,
        HashDTO: HashStrategy,
        "compress": CompressStrategy,
        CompressDTO: CompressStrategy,
        "verify": VerifyStrategy,
        VerifyDTO: VerifyStrategy,
        "backup": BackupStrategy,
        BackupDTO: BackupStrategy,
    }
    return repository_tag_map


@overload
def get_repository(repository_tag: Literal["oauth"]) -> OauthRepository: ...
@overload
def get_repository(repository_tag: type[OauthDTO]) -> OauthRepository: ...
@overload
def get_repository(repository_tag: Literal["scan"]) -> ScanStrategy: ...
@overload
def get_repository(repository_tag: type[ScanDTO]) -> ScanStrategy: ...
@overload
def get_repository(repository_tag: Literal["hash"]) -> HashStrategy: ...
@overload
def get_repository(repository_tag: type[HashDTO]) -> HashStrategy: ...
@overload
def get_repository(repository_tag: Literal["compress"]) -> CompressStrategy: ...
@overload
def get_repository(repository_tag: type[CompressDTO]) -> CompressStrategy: ...
@overload
def get_repository(repository_tag: Literal["verify"]) -> VerifyStrategy: ...
@overload
def get_repository(repository_tag: type[VerifyDTO]) -> VerifyStrategy: ...
@overload
def get_repository(repository_tag: Literal["backup"]) -> BackupStrategy: ...
@overload
def get_repository(repository_tag: type[BackupDTO]) -> BackupStrategy: ...



_instance_map = {}


def get_repository(repository_tag: str | DTOClass) -> StrategyInstance:
    global _instance_map
    repository_tag_map = get_repository_tag_map()
    repository_strategy = repository_tag_map.get(repository_tag)
    if repository_strategy is None:
        raise RepositoryException(f"Repository tag {repository_tag} not registered")
    if repository_tag in _instance_map:
        return _instance_map[repository_tag]
    _instance_map[repository_tag] = repository_strategy()
    return _instance_map[repository_tag]
