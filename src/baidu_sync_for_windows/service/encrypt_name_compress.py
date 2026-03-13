from baidu_sync_for_windows.dtos import EncryptNameCompressDTO
from baidu_sync_for_windows.config import get_config
from baidu_sync_for_windows.repository import get_default_repository
from baidu_sync_for_windows.logger import get_logger
from baidu_sync_for_windows.exception import CompressServiceException
from baidu_sync_for_windows.models import HashRecord
from baidu_sync_for_windows.exception.compress import (
    EncryptNameCompressServiceException,
)
from pathlib import Path
from dowhen import when
import pyzipper
from .scheduler import DiskSpaceCoordinator
from datetime import datetime
from dataclasses import dataclass

logger = get_logger(bind={"module_name": "encrypt_name_compress_service"})

@dataclass
class PreCheckResult:
    is_check_passed: bool
    check_message: str
    context: dict

def pre_check(source_id: int) -> PreCheckResult:
    repository = get_default_repository("encrypt_name_compress")
    if repository.is_processed(source_id):
        return PreCheckResult(is_check_passed=False, check_message=f"source id: {source_id} is already encrypting name and compressing, skip encrypting name and compressing", context={})
    record = repository.get_source_record_by_source_id(source_id)
    if record is None:
        return PreCheckResult(is_check_passed=False, check_message=f"source id: {source_id} not found", context={})
    if record.process_type == "manual":
        return PreCheckResult(is_check_passed=False, check_message=f"source id: {source_id} is manual, skip encrypting name and compressing", context={})
    if not Path(record.target_object_path).exists():
        return PreCheckResult(is_check_passed=False, check_message=f"source id: {source_id} target object path not found", context={})
    latested_service_record = repository.get_latest_service_record_by_source_id(source_id)
    if not latested_service_record:
        return PreCheckResult(is_check_passed=False, check_message=f"encrypt name and compress service latested service record of source id: {source_id} not found", context={})
    if latested_service_record.same_to_source_id != 0:
        return PreCheckResult(is_check_passed=False, check_message=f"source id: {source_id} is hash same to source id: {latested_service_record.same_to_source_id}, skip encrypting name and compressing", context={})
    return PreCheckResult(is_check_passed=True, check_message=f"source id: {source_id} is valid", context={'source_record': record, 'latested_service_record': latested_service_record})



def encrypt_name_compress_service(
    source_id: int, disk_space_coordinator: DiskSpaceCoordinator
) -> tuple[int, EncryptNameCompressDTO | None]:
    logger.log(
        "SERVICE_INFO",
        f"encrypting name and compressing object: {source_id} start,please wait...",
    )

    pre_check_result = pre_check(source_id)

    if not pre_check_result.is_check_passed:
        logger.log(
            "SERVICE_INFO",
            f'encrypt name and compress service pre check failed, reason: {pre_check_result.check_message},skip encrypting name and compressing',
        )
        return source_id, None
        
    record = pre_check_result.context['source_record']
    latested_service_record = pre_check_result.context['latested_service_record']
    disk_space_coordinator.acquire(
        "compress", int(record.target_object_size * 1.05), source_id
    )
    logger.info(
        f"source id: {source_id} disk space is acquired, start encrypting name and compressing"
    )
    encrypt_name = get_encrypt_name(latested_service_record)
    source_path = Path(record.target_object_path)
    if record.target_object_type == "file":
        compress_file_path = encrypt_and_compress_file(source_path, encrypt_name)
    elif record.target_object_type == "directory":
        compress_file_path = encrypt_and_compress_directory(source_path, encrypt_name)
    else:
        raise ValueError(
            f"target object type: {record.target_object_type} not supported"
        )
    compress_dto = EncryptNameCompressDTO(
        source_id=source_id,
        origin_file_name=source_path.name,
        encrypt_file_name=encrypt_name,
        compress_file_path=compress_file_path.absolute().as_posix(),
    )
    logger.log("SERVICE_INFO", f"compress file: {compress_file_path} is created")
    return source_id, compress_dto


def compress_file(
    source_path: Path,
    output_path: Path | str | None = None,
    password: str | None = None,
    compress_level: int | None = None,
    *,
    exclude_extensions: list[str] | None = None,
    is_random_salt: bool | None = None,
    **kwargs,
) -> Path:
    config = get_config()
    compress_file_name = output_path or create_default_compress_file_name(
        source_path, password
    )
    compress_level = (
        compress_level if compress_level is not None else config.compress.compress_level
    )
    exclude_extensions = (
        exclude_extensions
        if exclude_extensions is not None
        else config.compress.exclude_extensions
    )
    password = password if password is not None else config.compress.compress_password
    is_random_salt = (
        is_random_salt if is_random_salt is not None else config.compress.is_random_salt
    )
    logger.debug(
        f"compress file: {compress_file_name} is created, compress level: {compress_level}, exclude extensions: {exclude_extensions}, password: {password}, is random salt: {is_random_salt}"
    )
    handle_salt = None
    if not is_random_salt:
        handle_salt = when(
            pyzipper.zipfile_aes.AESZipEncrypter, "pwd_verify_length = 2"
        ).do(_add_self_salt)
    compress_file_path = init_compress_file_path(compress_file_name)
    logger.debug(f"compress file: {compress_file_path} is created")
    with pyzipper.AESZipFile(
        compress_file_path,
        "w",
        compression=pyzipper.ZIP_DEFLATED,
        compresslevel=compress_level,
    ) as zipf:
        if password:
            zipf.setpassword(password.encode("utf-8"))
            zipf.encryption = pyzipper.WZ_AES
        _add_object_to_compress_file(
            zipf, source_path, source_path.name, exclude_extensions
        )
    logger.log(
        "MODULE_INFO", f"compress file: {compress_file_path} is added to compress file"
    )

    if handle_salt:
        handle_salt.remove()
    return compress_file_path


def compress_directory(
    source_path: Path,
    output_path: Path | None = None,
    password: str | None = None,
    compress_level: int = 0,
    *,
    exclude_extensions: list[str] | None = None,
    is_random_salt: bool = True,
    **kwargs,
) -> Path:
    config = get_config()
    compress_file_name = output_path or create_default_compress_file_name(
        source_path, password
    )
    compress_level = (
        compress_level if compress_level is not None else config.compress.compress_level
    )
    exclude_extensions = (
        exclude_extensions
        if exclude_extensions is not None
        else config.compress.exclude_extensions
    )
    password = password if password is not None else config.compress.compress_password
    is_random_salt = (
        is_random_salt if is_random_salt is not None else config.compress.is_random_salt
    )
    logger.debug(
        f"compress directory: {compress_file_name} is created, compress level: {compress_level}, exclude extensions: {exclude_extensions}, password: {password}, is random salt: {is_random_salt}"
    )
    handle_salt = None
    if not is_random_salt:
        handle_salt = when(
            pyzipper.zipfile_aes.AESZipEncrypter, "pwd_verify_length = 2"
        ).do(_add_self_salt)
    compress_file_path = init_compress_file_path(compress_file_name)
    logger.debug(f"compress directory: {compress_file_path} is created")
    with pyzipper.AESZipFile(
        compress_file_path,
        "w",
        compression=pyzipper.ZIP_DEFLATED,
        compresslevel=compress_level,
    ) as zipf:
        if password:
            zipf.setpassword(password.encode("utf-8"))
            zipf.encryption = pyzipper.WZ_AES
        object_items = get_object_items(source_path, kwargs.get("object_items", None))
        for item in object_items:
            _add_object_to_compress_file(
                zipf,
                item,
                item.relative_to(source_path.parent).as_posix(),
                exclude_extensions,
            )
    logger.log(
        "MODULE_INFO",
        f"compress directory: {compress_file_path} is added to compress file",
    )

    if handle_salt:
        handle_salt.remove()
    return compress_file_path


def create_default_compress_file_name(
    source_path: Path, password: str | None = None
) -> str:
    config = get_config()
    compress_temp_dir = Path(config.compress.compress_temp_dir)
    date_str = datetime.now().strftime("%Y%m%d")
    if password is None:
        password = config.compress.compress_password
    parent_name = get_parent_name(source_path)
    if password:
        compress_file_name = (
            compress_temp_dir
            / date_str
            / parent_name
            / f"解压密码_{password}"
            / f"{source_path.name}.zip"
        )
    else:
        compress_file_name = (
            compress_temp_dir / date_str / parent_name / f"{source_path.name}.zip"
        )
    return compress_file_name.absolute().as_posix()


def create_encrypt_compress_file_name(
    source_path: Path, encrypt_name: str, password: str | None = None
) -> str:
    """根据加密后的文件名生成压缩文件路径，仅用于加密文件名压缩流程。"""
    config = get_config()
    compress_temp_dir = Path(config.compress.compress_temp_dir)
    date_str = datetime.now().strftime("%Y%m%d")
    if password is None:
        password = config.compress.compress_password
    parent_name = get_parent_name(source_path)
    if password:
        compress_file_name = (
            compress_temp_dir
            / date_str
            / parent_name
            / f"解压密码_{password}"
            / f"{encrypt_name}.zip"
        )
    else:
        compress_file_name = (
            compress_temp_dir / date_str / parent_name / f"{encrypt_name}.zip"
        )
    return compress_file_name.absolute().as_posix()


def get_parent_name(path: Path) -> str:
    if path.parent.name == "":
        return path.parent.absolute().as_posix().replace(":/", "盘根目录").upper()
    else:
        return path.parent.name


def init_compress_file_path(compress_file_name: Path | str) -> Path:
    compress_file_name = Path(compress_file_name)
    if compress_file_name.exists():
        compress_file_name.unlink()
    compress_file_name.parent.mkdir(parents=True, exist_ok=True)
    return compress_file_name


def _add_object_to_compress_file(
    zipf: pyzipper.AESZipFile,
    source_object_path: Path,
    arcname: str,
    exclude_extensions: list[str] | None = None,
) -> None:
    logger.debug(f"add object: {source_object_path} to compress file: {zipf.filename}")
    if exclude_extensions and source_object_path.suffix in exclude_extensions:
        logger.warning(f"object: {source_object_path} is excluded, skip add")
        return
    logger.debug(f"add object: {source_object_path} to compress file: {zipf.filename}")
    zipf.write(source_object_path, arcname)
    logger.debug(
        f"object: {source_object_path} is added to compress file: {zipf.filename}"
    )


def _add_self_salt(self) -> None:
    """为AES加密ZIP添加随机盐值（内部使用）

    通过dowhen库动态修改AESZipEncrypter类的pwd_verify_length属性，
    以支持任意长度的密码。

    Note:
        这是pyzipper库的特定hack，用于支持短密码
    """
    config = get_config()
    compress_salt = config.compress.compress_salt
    self.salt = compress_salt[self.salt_length]


def get_object_items(
    source_path: Path, object_items: list[Path | str] | None = None
) -> list[Path]:
    if object_items is None:
        return sorted([item for item in source_path.rglob("*")])
    else:
        return [Path(item) for item in object_items]


def get_encrypt_name(latested_service_record: HashRecord) -> str:
    """从最近一次服务记录中获取源路径与“加密文件名”。

    - 源路径来自 latested_service_record.source.target_object_path
    - 加密文件名优先使用 fast_hash/sha256/sha1/md5 字段，均为空时回退到源对象名
    """
    repository = get_default_repository("encrypt_name_compress")
    encrypt_name: str | None = None
    for attr in ("fast_hash", "md5", "sha1", "sha256"):
        value = getattr(latested_service_record, attr, None)
        if value and not repository.is_encrypt_name_used(value):
            encrypt_name = value
            break
    if not encrypt_name:
        logger.error(
            f"{latested_service_record.source_id} encrypt name invalid,please check hash record"
        )
        raise EncryptNameCompressServiceException(
            f"{latested_service_record.source_id} encrypt name invalid,please check hash record"
        )
    return encrypt_name


def encrypt_and_compress_file(source_path: Path, encrypt_name: str) -> Path:
    """对文件使用加密名称进行压缩，返回压缩文件路径。"""
    config = get_config()
    password = config.compress.compress_password
    output_path = create_encrypt_compress_file_name(source_path, encrypt_name, password)
    return compress_file(source_path, output_path=output_path, password=password)


def encrypt_and_compress_directory(source_path: Path, encrypt_name: str) -> Path:
    """对目录使用加密名称进行压缩，返回压缩文件路径。"""
    config = get_config()
    password = config.compress.compress_password
    output_path = create_encrypt_compress_file_name(source_path, encrypt_name, password)
    return compress_directory(
        source_path, output_path=Path(output_path), password=password
    )
