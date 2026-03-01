from baidu_sync_for_windows.dtos import CompressDTO
from baidu_sync_for_windows.config import get_config
from baidu_sync_for_windows.service.hash import hash_file
from baidu_sync_for_windows.repository import get_default_repository
from baidu_sync_for_windows.logger import get_logger
from baidu_sync_for_windows.exception import CompressServiceException
from pathlib import Path
from dowhen import when
import pyzipper
from .scheduler import DiskSpaceCoordinator
from datetime import datetime

logger = get_logger(bind={"module_name": "compress_service"})


def compress_service(
    source_id: int, disk_space_coordinator: DiskSpaceCoordinator
) -> tuple[int, CompressDTO | None]:
    logger.log('SERVICE_INFO',f"compressing object: {source_id} start,please wait...")
    repository = get_default_repository()
    if repository.is_processed(CompressDTO, source_id):
        logger.log('SERVICE_INFO',f"source id: {source_id} is already compressed, skip compress")
        return source_id, None
    record = repository.get_source_record_by_source_id(CompressDTO, source_id)
    if record is None:
        raise CompressServiceException(f"source id: {source_id} not found")
    if record.process_type == "manual":
        logger.log('SERVICE_INFO',f"source id: {source_id} is manual, skip compress")
        return source_id, None
    disk_space_coordinator.acquire("compress", int(record.target_object_size * 1.05))
    logger.info(f"source id: {source_id} disk space is acquired, start compress")
    source_path = Path(record.target_object_path)
    if record.target_object_type == "file":
        compress_file_path, compress_file_hash = compress_file(source_path)
    elif record.target_object_type == "directory":
        compress_file_path, compress_file_hash = compress_directory(source_path)
    else:
        raise ValueError(
            f"target object type: {record.target_object_type} not supported"
        )
    compress_dto = CompressDTO(
        source_id=source_id,
        compress_file_path=compress_file_path.absolute().as_posix(),
        md5=compress_file_hash,
    )
    logger.log('SERVICE_INFO',f"compress file: {compress_file_path} is created, hash: {compress_file_hash}")
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
) -> tuple[Path, str]:
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
    logger.debug(f"compress file: {compress_file_name} is created, compress level: {compress_level}, exclude extensions: {exclude_extensions}, password: {password}, is random salt: {is_random_salt}")
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
    logger.log('MODULE_INFO',f"compress file: {compress_file_path} is added to compress file")
    logger.log('MODULE_INFO',f"start to hash compress file: {compress_file_path}")
    compress_file_hash = hash_file(
        compress_file_path, config.compress.verify_hash_algorithm
    )
    logger.log('MODULE_INFO',f"compress file: {compress_file_path} is hashed, hash: {compress_file_hash}")
    if handle_salt:
        handle_salt.remove()
    return compress_file_path, compress_file_hash


def compress_directory(
    source_path: Path,
    output_path: Path | None = None,
    password: str | None = None,
    compress_level: int = 0,
    *,
    exclude_extensions: list[str] | None = None,
    is_random_salt: bool = True,
    **kwargs,
) -> tuple[Path, str]:
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
    logger.debug(f"compress directory: {compress_file_name} is created, compress level: {compress_level}, exclude extensions: {exclude_extensions}, password: {password}, is random salt: {is_random_salt}")
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
    logger.log('MODULE_INFO',f"compress directory: {compress_file_path} is added to compress file")
    logger.log('MODULE_INFO',f"start to hash compress directory: {compress_file_path}")
    compress_file_hash = hash_file(
        compress_file_path, config.compress.verify_hash_algorithm
    )
    logger.log('MODULE_INFO',f"compress directory: {compress_file_path} is hashed, hash: {compress_file_hash}")
    if handle_salt:
        handle_salt.remove()
    return compress_file_path, compress_file_hash


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
            compress_temp_dir
            / date_str
            / parent_name
            / f"{source_path.name}.zip"
        )
    return compress_file_name.absolute().as_posix()
def get_parent_name(path: Path) -> str:
    if path.parent.name == '':
        return path.parent.absolute().as_posix().replace(':/', '盘根目录').upper()
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
    logger.debug(f"object: {source_object_path} is added to compress file: {zipf.filename}")

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
