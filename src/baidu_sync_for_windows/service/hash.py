from asyncio import as_completed
from functools import cache
from baidu_sync_for_windows.dtos import HashDTO
from baidu_sync_for_windows.config import get_config
from baidu_sync_for_windows.repository import get_default_repository
from baidu_sync_for_windows.logger import get_logger
import hashlib
from typing import overload
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import threading
config = get_config()
logger = get_logger(bind={'service_name':'hash_service'})

def hash_service(source_object_id: int) -> HashDTO: ...







@overload
def hash_file(file_path: Path, algorithm: str)->str: ...
@overload
def hash_file(file_path: dict[str, int], algorithm: str)->str: ...
@overload
def hash_file(file_path:Path, algorithm: str,max_threads:int)->str:...
@overload
def hash_file(file_path:dict[str, int], algorithm: str,max_threads:int)->str:...

def hash_file(file_path: Path | dict[str, int], algorithm: str,max_threads:int=0)->str:
    logger.info(f"hash_file: {file_path}, algorithm: {algorithm}, max_threads: {max_threads}")
    if isinstance(file_path, Path):
        target_path = file_path
    else:
        target_path = Path(list(file_path.keys())[0])
    if max_threads == 0:
        index,hash_obj =  _hash_file_single_thread(target_path, algorithm, 0)
    else:
        index,hash_obj = _hash_file_thread(target_path, algorithm, max_threads)
    result = hash_obj.hexdigest().lower()
    logger.info(f"hash_file: {file_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}")
    return result

def _hash_file_single_thread(target_path: Path, algorithm: str,index:int = 0):
    logger.log("MODULE_INFO",f"hash_file_single_thread: {target_path}, algorithm: {algorithm}, index: {index}")
    hash_obj = hashlib.new(algorithm)
    with open(target_path, "rb") as f:
        while True:
            data = f.read(config.hash.hash_chunk_size)
            if not data:
                break
            hash_obj.update(data)
    result = hash_obj
    logger.log("MODULE_INFO",f"hash_file_single_thread: {target_path}, algorithm: {algorithm}, index: {index}, result: {result}")
    return index,result

def _hash_file_thread(target_path: Path, algorithm: str, max_threads: int):
    logger.log("MODULE_INFO",f"hash_file_thread: {target_path}, algorithm: {algorithm}, max_threads: {max_threads}")
    index,result = _hash_file_single_thread(target_path, algorithm, 0)
    logger.log("MODULE_INFO",f"hash_file_thread: {target_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}")
    return index,result

@overload
def hash_folder(folder_path: Path, algorithm: str)->str: ...
@overload
def hash_folder(folder_path: dict[str, int], algorithm: str)->str: ...
@overload
def hash_folder(folder_path: Path, algorithm: str,max_threads:int)->str: ...
@overload
def hash_folder(folder_path: dict[str, int], algorithm: str,max_threads:int)->str: ...

def hash_folder(folder_path: Path | dict[str, int], algorithm: str,max_threads:int=0)->str:
    logger.info(f"hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}")
    if isinstance(folder_path, Path):
        files = sorted([f for f in folder_path.rglob("*") if f.is_file()])
    else:
        files = sorted([Path(f) for f in folder_path.keys()])
    folder_hash_object = hashlib.new(algorithm)
    if max_threads == 0:
        for file in files:
            _,hash_obj = _hash_file_single_thread(file, algorithm)
            folder_hash_object.update(hash_obj.digest())
        result = folder_hash_object.hexdigest().lower()
        logger.info(f"hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}")
        return result
    else:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            results = executor.map(_hash_file_single_thread,files, [algorithm] * len(files),range(len(files)))
            sorted_results = sorted(results, key=lambda x: x[0])
            for _,hash_obj in sorted_results:
                folder_hash_object.update(hash_obj.digest())
        result = folder_hash_object.hexdigest().lower()
        logger.info(f"hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}")
        return result


@overload
def fast_hash_folder(folder_path: Path, algorithm: str)->str: ...
@overload
def fast_hash_folder(folder_path: dict[str, int], algorithm: str)->str: ...
@overload
def fast_hash_folder(folder_path: Path, algorithm: str,max_threads:int)->str: ...
@overload
def fast_hash_folder(folder_path: dict[str, int], algorithm: str,max_threads:int)->str: ...

def fast_hash_folder(folder_path: Path | dict[str, int], algorithm: str,max_threads:int=0)->str:
    logger.info(f"fast_hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}")
    if isinstance(folder_path, Path):
        files = sorted([f for f in folder_path.rglob("*") if f.is_file()])
    else:
        files = sorted([Path(f) for f in folder_path.keys()])
    fast_hash_object = hashlib.new(config.hash.folder_fast_hash_algorithm)
    if max_threads == 0:
        for file in files:
            _,hash_obj = _calculate_fast_hash(file, algorithm)
            fast_hash_object.update(hash_obj.digest())
        result = fast_hash_object.hexdigest().lower()
        logger.info(f"fast_hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}")
        return result
    else:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            results = executor.map(_calculate_fast_hash, files, [algorithm] * len(files),range(len(files)))
            sorted_results = sorted(results, key=lambda x: x[0])
            for _,hash_obj in sorted_results:
                fast_hash_object.update(hash_obj.digest())
        result = fast_hash_object.hexdigest().lower()
        logger.info(f"fast_hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}")
        return result


def _calculate_fast_hash(file: Path, algorithm: str,index:int = 0):
    if file.stat().st_size < config.hash.fast_hash_chunk_size:
        result =  _calculate_fast_hash_small(file, algorithm)
    elif file.stat().st_size < config.hash.fast_hash_chunk_size * 5:
        result = _calculate_fast_hash_medium(file, algorithm)
    else:
        result = _calculate_fast_hash_large(file, algorithm)

    return index,result

def _calculate_fast_hash_small(file: Path, algorithm: str):
    fast_hash_object = hashlib.new(algorithm)
    with open(file, "rb") as f:
        data = f.read(config.hash.fast_hash_chunk_size)
        fast_hash_object.update(data)
    return fast_hash_object

def _calculate_fast_hash_medium(file: Path, algorithm: str):
    fast_hash_object = hashlib.new(algorithm)
    with open(file, "rb") as f:
        first_data = f.read(config.hash.fast_hash_chunk_size)
        fast_hash_object.update(first_data)
        # 从文件未读取一个块的数据
        last_data = f.seek(-config.hash.fast_hash_chunk_size, 2)
        last_data = f.read(config.hash.fast_hash_chunk_size)
        fast_hash_object.update(last_data)
    return fast_hash_object

def _calculate_fast_hash_large(file: Path, algorithm: str):
    fast_hash_object = hashlib.new(algorithm)
    with open(file, "rb") as f:
        first_data = f.read(config.hash.fast_hash_chunk_size)
        fast_hash_object.update(first_data)
        # 从文件最中间读取一个数据块
        middle_data = f.seek(f.tell() // 2)
        middle_data = f.read(config.hash.fast_hash_chunk_size)
        fast_hash_object.update(
            middle_data
        )
        # 从文件未读取一个块的数据
        last_data = f.seek(-config.hash.fast_hash_chunk_size, 2)
        last_data = f.read(config.hash.fast_hash_chunk_size)
        fast_hash_object.update(last_data)
    return fast_hash_object


def hash_folder_cache(folder_path: Path | dict[str, int], algorithm: str,max_threads:int=1)->str:
    from src.baidu_sync_for_windows.cache import CacheService
    cache_service = CacheService()
    service_tag = f"hash_folder_{algorithm}_{max_threads}_{threading.current_thread().native_id}"
    logger.info(f"hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}")
    if isinstance(folder_path, Path):
        files = sorted([f for f in folder_path.rglob("*") if f.is_file()])
    else:
        files = sorted([Path(f) for f in folder_path.keys()])
    results = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        results = [executor.submit(_hash_file_single_thread, file, algorithm, index) for index,file in enumerate(files)]
        hash_object = hashlib.new(algorithm)
        hashed_index = 0
        for result in as_completed(results):
            index,hash_obj = result.result()
            logger.log("MODULE_INFO",f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, index: {index} completed")
            if index == hashed_index:
                hash_object.update(hash_obj.digest())
                logger.log("MODULE_INFO",f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, hash {index} immediately")
                hashed_index += 1
            else:
                cache_service.set_cache_record(service_tag, f"{index}",  _decode_bytes_to_str(hash_obj.digest()))
                logger.log("MODULE_INFO",f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, hash {index} cached")
                cache_value = cache_service.get_cache_record(service_tag, f"{hashed_index}")
                logger.log("MODULE_INFO",f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, try to get hash {hashed_index} cached value: {cache_value}")
                if cache_value is not None:
                    hash_object.update(_encode_str_to_bytes(cache_value))
                    logger.log("MODULE_INFO",f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, hash {hashed_index} cached value: {cache_value} when index is {index}")
                    hashed_index += 1
    if hashed_index < len(files):
        logger.log("MODULE_INFO",f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, hashed_index is {hashed_index}, try to get cached value from index {hashed_index} to {len(files)-1}")
        for index in range(hashed_index, len(files)):
            cache_value = cache_service.get_cache_record(service_tag, f"{index}")
            if cache_value is None:
                logger.error(f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, cache_value is None for index: {index}")
                raise ValueError(f"cache_value is None for index: {index}")
            hash_object.update(_encode_str_to_bytes(cache_value))
            hashed_index += 1
    result = hash_object.hexdigest().lower()
    logger.info(f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}")
    return result

def _decode_bytes_to_str(data: bytes)->str:
    return data.hex()

def _encode_str_to_bytes(data: str)->bytes:
    return bytes.fromhex(data)