from pathlib import Path
from typing import Literal
from baidu_sync_for_windows.dtos import ScanDTO
from baidu_sync_for_windows.exception import ScanServiceException
from baidu_sync_for_windows.logger import get_logger
from baidu_sync_for_windows.config import get_config
logger = get_logger(bind={'service_name':'scan'})

def _check_file_path(file_path:str|Path)->Path:
    file_path = Path(file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise ScanServiceException(f"File not found: {file_path}")
    return file_path


def scan_service(target_path_list:list[str|Path])->list[ScanDTO]:
    result = []
    for target_path in target_path_list:
        result.extend(scan_object(target_path))
    return result

def scan_object(file_path:str|Path)->list[ScanDTO]:
    file_path = _check_file_path(file_path)
    if file_path.is_file():
        return [_scan_file(file_path)]

    result = []
    items = sorted(file_path.iterdir())
    for item in items:
        if item.is_file():
            result.append(_scan_file(item))
        elif item.is_dir():
            result.append(_scan_directory(item))
        else:
            logger.warning(f"Unknown item type: {item}")
            raise ScanServiceException(f"Unknown item type: {item}")
    return result

def _get_process_type(object_size: int) -> Literal["auto", "manual"]:
    oversize = get_config().scan.oversize
    if object_size > oversize:
        return "manual"
    elif object_size == 0:
        return "manual"
    else:
        return "auto"

def _scan_file(file_path:Path)->ScanDTO:
    object_path = file_path
    target_object_path_str = object_path.resolve().as_posix()
    object_size = object_path.stat().st_size
    process_type = _get_process_type(object_size)
    return ScanDTO(
        drive_letter=get_config().drive_letter,
        target_object_path=target_object_path_str,
        target_object_name=object_path.name,
        target_object_type=object_path.is_dir() and "directory" or "file",
        target_object_size=object_size,
        process_type=process_type,
        target_object_items_count=1,
        target_object_items={
            target_object_path_str: object_path.stat().st_mtime_ns
        },
    )


def _scan_directory(directory_path:Path)->ScanDTO:
    object_path = directory_path
    target_object_path_str = object_path.resolve().as_posix()
    sorted_items = sorted([item for item in object_path.rglob("*")])
    object_size = sum([item.stat().st_size for item in sorted_items if item.is_file()])
    items_count = len(sorted_items)
    items = {
        item.resolve().as_posix(): item.stat().st_mtime_ns for item in sorted_items
    }
    process_type = _get_process_type(object_size)
    return ScanDTO(
        drive_letter=get_config().drive_letter,
        target_object_path=target_object_path_str,
        target_object_name=object_path.name,
        target_object_type="directory",
        target_object_size=object_size,
        process_type=process_type,
        target_object_items_count=items_count,
        target_object_items=items,
    )


if __name__ == "__main__":
    target_path_list = [
        r"E:\OneDrive\2025年项目\智擎领途公司\公司基本信息照片",
        r"D:\测试AI运行",
    ]
    result = scan_service(target_path_list)
    print(result)
