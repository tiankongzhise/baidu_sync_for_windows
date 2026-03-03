from baidu_sync_for_windows.dtos import VerifyDTO,HashDTO
from pathlib import Path
import pyzipper
from baidu_sync_for_windows.config import get_config
from baidu_sync_for_windows.service.hash import hash_object
from baidu_sync_for_windows.repository import get_default_repository
from baidu_sync_for_windows.exception import VerifyServiceException
from baidu_sync_for_windows.service.scan import _scan_file,_scan_directory
from baidu_sync_for_windows.logger import get_logger
from time import time_ns
import shutil
from .scheduler import DiskSpaceCoordinator
logger = get_logger(bind={'service_name':'verify'})
def verify_service(source_object_id:int,disk_space_coordinator:DiskSpaceCoordinator)->tuple[int, VerifyDTO | None]:
    logger.log('SERVICE_INFO',f"verify object start, source object id: {source_object_id}")
    repository = get_default_repository('verify')
    if repository.is_processed(source_object_id):
        logger.log('SERVICE_INFO',f"source object id: {source_object_id} is already verified, skip verify")
        return source_object_id, None
    source_record = repository.get_source_record_by_source_id(source_object_id)
    logger.debug(f"source object id: {source_object_id} source record: {source_record}")
    if source_record.process_type == "manual": # type: ignore
        logger.log('SERVICE_INFO',f"source object id: {source_object_id} is manual, skip verify")
        return source_object_id, None
    latest_record = repository.get_latest_service_record_by_source_id(source_object_id)
    logger.debug(f"source object id: {source_object_id} latest service record: {latest_record}")

    if latest_record is None:
        raise VerifyServiceException(f"compress service record not found for source object id: {source_object_id}")
    with disk_space_coordinator.reserve('verify', int(source_record.target_object_size*1.05)):# type: ignore
        logger.log('SERVICE_INFO',f"verify object reserve disk space success, source object id: {source_object_id}")
        unzip_verify_object_path = unzip_verify_object(Path(latest_record.compress_file_path))
        logger.log('SERVICE_INFO',f"verify object unzip compress file success, source object id: {source_object_id}")
        hash_dto = calculate_unzip_verify_object_hash(source_object_id,unzip_verify_object_path)
        logger.log('SERVICE_INFO',f"verify object calculate unzip verify object hash success, source object id: {source_object_id}")
        hash_temp = hash_dto.model_dump()
        hash_temp.pop('source_id')
        verify_result = repository.is_verify_success(hash_dto)
        verify_dto = VerifyDTO(source_id=source_object_id, verify_compress_file_path=latest_record.compress_file_path, verify_result=verify_result, **hash_temp)
        logger.log('SERVICE_INFO',f"verify object create verify dto success, source object id: {source_object_id}")
        clean_unzip_verify_object(unzip_verify_object_path)
        logger.log('SERVICE_INFO',f"verify object clean unzip verify object success, source object id: {source_object_id}")
        logger.log('SERVICE_INFO',f"verify object end, source object id: {source_object_id}")
        return source_object_id, verify_dto

def unzip_verify_object(compress_file_path:Path)->Path:
    config = get_config()
    unzip_verify_object_path = Path(config.verify.uncompress_temp_dir) / f"{time_ns()}" / compress_file_path.name.replace(".zip", "")
    unzip_verify_object_path.mkdir(parents=True, exist_ok=True)
    password = config.verify.uncompress_password
    logger.debug(f"unzip verify object start, compress file path: {compress_file_path}, unzip verify object path: {unzip_verify_object_path}, password: {password}")
    with pyzipper.AESZipFile(compress_file_path,mode = 'r') as zip_file:
        if password:
            zip_file.setpassword(password.encode('utf-8'))
        zip_file.extractall(unzip_verify_object_path)
    logger.debug(f"unzip verify object end, compress file path: {compress_file_path}, unzip verify object path: {unzip_verify_object_path}, password: {password}")
    return unzip_verify_object_path

def calculate_unzip_verify_object_hash(source_id:int,unzip_verify_object_path:Path)->HashDTO:
    logger.debug(f"calculate unzip verify object hash start, source id: {source_id}, unzip verify object path: {unzip_verify_object_path}")
    if unzip_verify_object_path.is_file():
        logger.debug(f"calculate unzip verify object hash is file, unzip verify object path: {unzip_verify_object_path}")
        scan_dto = _scan_file(unzip_verify_object_path)
        logger.debug("calculate unzip verify object hash is file, scan dto done")
    else:
        logger.debug(f"calculate unzip verify object hash is directory, unzip verify object path: {unzip_verify_object_path}")
        scan_dto = _scan_directory(unzip_verify_object_path)
        logger.debug("calculate unzip verify object hash is directory, scan dto done")
    hash_dto = hash_object(source_id, scan_dto)
    return hash_dto

def clean_unzip_verify_object(unzip_verify_object_path:Path):
    logger.info(f"clean unzip verify object start, unzip verify object path: {unzip_verify_object_path}")
    if unzip_verify_object_path.is_file():
        unzip_verify_object_path.unlink()
        logger.info(f"clean unzip verify object is file, unzip verify object path: {unzip_verify_object_path}")
    else:
        shutil.rmtree(unzip_verify_object_path.parent)
        logger.info(f"clean unzip verify object is directory, unzip verify object path: {unzip_verify_object_path}")
    logger.info(f"clean unzip verify object end, unzip verify object path: {unzip_verify_object_path}")
