from baidu_sync_for_windows.dtos import HashDTO
from baidu_sync_for_windows.config import get_config
from baidu_sync_for_windows.repository import get_default_repository
from baidu_sync_for_windows.logger import get_logger
from baidu_sync_for_windows.cache import CacheService
import hashlib
from typing import overload
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 修改为懒加载方式

config = get_config()
logger = get_logger(bind={"service_name": "hash_service"})


def hash_service(source_id: int) -> tuple[int, HashDTO | None]:
    repository = get_default_repository()
    record = repository.get_source_record_by_source_id(HashDTO, source_id)
    if record is None:
        raise ValueError(f"source id: {source_id} not found")
    if record.process_type == "manual":
        logger.info(f"source id: {source_id} is manual, skip hash")
        return source_id, None
    target_object_path = Path(record.target_object_path)
    target_path_type = record.target_object_type
    target_object_items_count = record.target_object_items_count
    target_object_items = record.target_object_items
    hash_func = None
    if target_object_items_count > config.hash.folder_overcount:
        hash_func = fast_hash_folder
        hash_value = hash_func(
            target_object_path, config.hash.folder_fast_hash_algorithm,items=target_object_items
        )
        return source_id, HashDTO(source_id=source_id, fast_hash=hash_value)

    if target_path_type == "file":
        hash_func = hash_file
    elif target_path_type == "directory":
        hash_func = hash_folder
    else:
        raise ValueError(f"target path type: {target_path_type} not supported")
    hash_result = {}
    for algorithm in config.hash.algorithm:
        hash_result[algorithm] = hash_func(target_object_path, algorithm,items=target_object_items)
    return source_id, HashDTO(source_id=source_id, **hash_result)


@overload
def hash_file(file_path: Path, algorithm: str) -> str: ...
@overload
def hash_file(file_path: Path, algorithm: str, *, items: dict[str, int]) -> str: ...
@overload
def hash_file(file_path: Path, algorithm: str, *, max_threads: int) -> str: ...
@overload
def hash_file(
    file_path: Path, algorithm: str, *, items: dict[str, int], max_threads: int
) -> str: ...


def hash_file(*args, **kwargs) -> str:
    file_path: Path = None  # type: ignore
    algorithm: str = None  # type: ignore
    items: dict[str, int] = None  # type: ignore
    max_threads: int = None  # type: ignore
    match args:
        case (file_path_arg, algorithm_arg):
            file_path = file_path_arg
            algorithm = algorithm_arg
        case (file_path_arg,):
            file_path = file_path_arg
        case _:
            raise ValueError(f"invalid arguments: {args}")
    match kwargs:
        case {"file_path": file_path_arg}:
            file_path = file_path_arg
        case {"algorithm": algorithm_arg}:
            algorithm = algorithm_arg
        case {"items": items_arg}:
            items = items_arg
        case {"max_threads": max_threads_arg}:
            max_threads = max_threads_arg
        case _:
            raise ValueError(f"invalid arguments: {kwargs}")
    logger.info(
        f"hash_file: {file_path}, algorithm: {algorithm}, max_threads: {max_threads}"
    )
    if items is None:
        target_path = file_path
    else:
        target_path = Path(list(items.keys())[0])
    if max_threads == 0:
        index, hash_obj = _hash_file_single_thread(target_path, algorithm, 0)
    else:
        index, hash_obj = _hash_file_thread(target_path, algorithm, max_threads)
    result = hash_obj.hexdigest().lower()
    logger.info(
        f"hash_file: {file_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}"
    )
    return result


def _hash_file_single_thread(target_path: Path, algorithm: str, index: int = 0):
    logger.log(
        "MODULE_INFO",
        f"hash_file_single_thread: {target_path}, algorithm: {algorithm}, index: {index}",
    )
    hash_obj = hashlib.new(algorithm)
    with open(target_path, "rb") as f:
        while True:
            data = f.read(config.hash.hash_chunk_size)
            if not data:
                break
            hash_obj.update(data)
    result = hash_obj
    logger.log(
        "MODULE_INFO",
        f"hash_file_single_thread: {target_path}, algorithm: {algorithm}, index: {index}, result: {result}",
    )
    return index, result


def _hash_file_thread(target_path: Path, algorithm: str, max_threads: int):
    logger.log(
        "MODULE_INFO",
        f"hash_file_thread: {target_path}, algorithm: {algorithm}, max_threads: {max_threads}",
    )
    index, result = _hash_file_single_thread(target_path, algorithm, 0)
    logger.log(
        "MODULE_INFO",
        f"hash_file_thread: {target_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}",
    )
    return index, result


@overload
def hash_folder(folder_path: Path, algorithm: str) -> str: ...
@overload
def hash_folder(folder_path: Path, algorithm: str, *, items: dict[str, int]) -> str: ...
@overload
def hash_folder(folder_path: Path, algorithm: str, *, max_threads: int) -> str: ...
@overload
def hash_folder(
    folder_path: Path, algorithm: str, *, items: dict[str, int], max_threads: int
) -> str: ...


def hash_folder(*args, **kwargs) -> str:
    folder_path: Path = None  # type: ignore
    algorithm: str = None  # type: ignore
    items: dict[str, int] = None  # type: ignore
    max_threads: int = None  # type: ignore
    match args:
        case (folder_path_arg, algorithm_arg):
            folder_path = folder_path_arg
            algorithm = algorithm_arg
        case (folder_path_arg,):
            folder_path = folder_path_arg
        case _:
            raise ValueError(f"invalid arguments: {args}")
    match kwargs:
        case {"folder_path": folder_path_arg}:
            folder_path = folder_path_arg
        case {"algorithm": algorithm_arg}:
            algorithm = algorithm_arg
        case {"items": items_arg}:
            items = items_arg
        case {"max_threads": max_threads_arg}:
            max_threads = max_threads_arg
        case _:
            raise ValueError(f"invalid arguments: {kwargs}")
    if items is None:
        files = sorted([f for f in folder_path.rglob("*") if f.is_file()])
    else:
        files = sorted([Path(f) for f in items.keys() if Path(f).is_file()])
    folder_hash_object = hashlib.new(algorithm)
    if max_threads == 0:
        for file in files:
            _, hash_obj = _hash_file_single_thread(file, algorithm)
            folder_hash_object.update(hash_obj.digest())
        result = folder_hash_object.hexdigest().lower()
        logger.info(
            f"hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}"
        )
        return result
    else:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            results = executor.map(
                _hash_file_single_thread,
                files,
                [algorithm] * len(files),
                range(len(files)),
            )
            sorted_results = sorted(results, key=lambda x: x[0])
            for _, hash_obj in sorted_results:
                folder_hash_object.update(hash_obj.digest())
        result = folder_hash_object.hexdigest().lower()
        logger.info(
            f"hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result}"
        )
        return result


@overload
def fast_hash_folder(
    folder_path: Path, algorithm: str = config.hash.folder_fast_hash_algorithm
) -> str: ...
@overload
def fast_hash_folder(
    folder_path: Path,
    algorithm: str = config.hash.folder_fast_hash_algorithm,
    *,
    items: dict[str, int],
) -> str: ...
@overload
def fast_hash_folder(
    folder_path: Path,
    algorithm: str = config.hash.folder_fast_hash_algorithm,
    *,
    max_threads: int = 1,
) -> str: ...
@overload
def fast_hash_folder(
    folder_path: Path,
    algorithm: str = config.hash.folder_fast_hash_algorithm,
    *,
    items: dict[str, int],
    max_threads: int = 1,
) -> str: ...


def fast_hash_folder(*args, **kwargs) -> str:
    folder_path: Path = None  # type: ignore
    algorithm: str = None  # type: ignore
    items: dict[str, int] = None  # type: ignore
    max_threads: int = None  # type: ignore
    match args:
        case (folder_path_arg, algorithm_arg):
            folder_path = folder_path_arg
            algorithm = algorithm_arg
        case (folder_path_arg,):
            folder_path = folder_path_arg
        case _:
            raise ValueError(f"invalid arguments: {args}")
    match kwargs:
        case {"folder_path": folder_path_arg}:
            folder_path = folder_path_arg
        case {"algorithm": algorithm_arg}:
            algorithm = algorithm_arg
        case {"items": items_arg}:
            items = items_arg
        case {"max_threads": max_threads_arg}:
            max_threads = max_threads_arg
        case _:
            raise ValueError(f"invalid arguments: {kwargs}")

    if max_threads == 0:
        return fast_hash_single_thread(folder_path, algorithm, items)
    else:
        return fast_hash_folder_cache(folder_path, algorithm, max_threads, items)


def fast_hash_folder_cache(
    folder_path: Path,
    algorithm: str = config.hash.folder_fast_hash_algorithm,
    max_threads: int = 1,
    items: dict[str, int] |None= None,
) -> str:
    logger.info(
        f"fast_hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}"
    )
    if items is None:
        files = sorted([f for f in folder_path.rglob("*") if f.is_file()])
    else:
        files = sorted([Path(f) for f in items.keys() if Path(f).is_file()])
    fast_hash_object = hashlib.new(algorithm)
    hashed_index = 0
    service_tag = f"fast_hash_folder_{algorithm}_{max_threads}_{threading.current_thread().native_id}"
    cache_service = CacheService(service_tag=service_tag)
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        results = [
            executor.submit(_calculate_fast_hash, file, algorithm, index)
            for index, file in enumerate(files)
        ]
        for result in as_completed(results):
            index, hash_obj = result.result()
            if index == hashed_index:
                fast_hash_object.update(hash_obj.digest())
                hashed_index += 1
            else:
                cache_service.set_cache_record(
                    f"{index}", _decode_bytes_to_str(hash_obj.digest())
                )
                cache_value = cache_service.get_cache_record(
                    service_tag, f"{hashed_index}"
                )
                if cache_value is not None:
                    fast_hash_object.update(_encode_str_to_bytes(cache_value))
                    hashed_index += 1
    if hashed_index < len(files):
        for index in range(hashed_index, len(files)):
            cache_value = cache_service.get_cache_record(service_tag, f"{index}")
            if cache_value is None:
                logger.error(
                    f"fast_hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, cache_value is None for index: {index}"
                )
                raise ValueError(f"cache_value is None for index: {index}")
            fast_hash_object.update(_encode_str_to_bytes(cache_value))
            hashed_index += 1
    result = fast_hash_object.hexdigest().lower()
    logger.info(
        f"fast_hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result},objects: {len(files)}"
    )
    return result


def fast_hash_single_thread(
    folder_path: Path,
    algorithm: str = config.hash.folder_fast_hash_algorithm,
    items: dict[str, int] |None= None,
):
    logger.info(f"fast_hash_single_thread: {folder_path}, algorithm: {algorithm}")
    fast_hash_object = hashlib.new(algorithm)
    if items is None:
        files = sorted([f for f in folder_path.rglob("*") if f.is_file()])
    else:
        files = sorted([Path(f) for f in items.keys() if Path(f).is_file()])
    for index, file in enumerate(files):
        _, hash_obj = _calculate_fast_hash(file, algorithm, index)
        fast_hash_object.update(hash_obj.digest())
    result = fast_hash_object.hexdigest().lower()
    logger.log(
        "MODULE_INFO",
        f"fast_hash_single_thread: {folder_path}, algorithm: {algorithm}, result: {result},objects: {len(files)}",
    )
    return result


def _calculate_fast_hash(file: Path, algorithm: str, index: int = 0):
    if file.stat().st_size < config.hash.fast_hash_chunk_size:
        result = _calculate_fast_hash_small(file, algorithm)
    elif file.stat().st_size < config.hash.fast_hash_chunk_size * 5:
        result = _calculate_fast_hash_medium(file, algorithm)
    else:
        result = _calculate_fast_hash_large(file, algorithm)

    return index, result


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
        fast_hash_object.update(middle_data)
        # 从文件未读取一个块的数据
        last_data = f.seek(-config.hash.fast_hash_chunk_size, 2)
        last_data = f.read(config.hash.fast_hash_chunk_size)
        fast_hash_object.update(last_data)
    return fast_hash_object


def hash_folder_cache(
    folder_path: Path | dict[str, int], algorithm: str, max_threads: int = 1
) -> str:
    cache_service = CacheService()
    service_tag = (
        f"hash_folder_{algorithm}_{max_threads}_{threading.current_thread().native_id}"
    )
    logger.info(
        f"hash_folder: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}"
    )
    if isinstance(folder_path, Path):
        files = sorted([f for f in folder_path.rglob("*") if f.is_file()])
    else:
        files = sorted([Path(f) for f in folder_path.keys() if Path(f).is_file()])
    results = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        results = [
            executor.submit(_hash_file_single_thread, file, algorithm, index)
            for index, file in enumerate(files)
        ]
        hash_object = hashlib.new(algorithm)
        hashed_index = 0
        for result in as_completed(results):
            index, hash_obj = result.result()
            logger.log(
                "MODULE_INFO",
                f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, index: {index} completed",
            )
            if index == hashed_index:
                hash_object.update(hash_obj.digest())
                logger.log(
                    "MODULE_INFO",
                    f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, hash {index} immediately",
                )
                hashed_index += 1
            else:
                cache_service.set_cache_record(
                    service_tag, f"{index}", _decode_bytes_to_str(hash_obj.digest())
                )
                logger.log(
                    "MODULE_INFO",
                    f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, hash {index} cached",
                )
                cache_value = cache_service.get_cache_record(
                    service_tag, f"{hashed_index}"
                )
                logger.log(
                    "MODULE_INFO",
                    f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, try to get hash {hashed_index} cached value: {cache_value}",
                )
                if cache_value is not None:
                    hash_object.update(_encode_str_to_bytes(cache_value))
                    logger.log(
                        "MODULE_INFO",
                        f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, hash {hashed_index} cached value: {cache_value} when index is {index}",
                    )
                    hashed_index += 1
    if hashed_index < len(files):
        logger.log(
            "MODULE_INFO",
            f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, hashed_index is {hashed_index}, try to get cached value from index {hashed_index} to {len(files) - 1}",
        )
        for index in range(hashed_index, len(files)):
            cache_value = cache_service.get_cache_record(service_tag, f"{index}")
            if cache_value is None:
                logger.error(
                    f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, cache_value is None for index: {index}"
                )
                raise ValueError(f"cache_value is None for index: {index}")
            hash_object.update(_encode_str_to_bytes(cache_value))
            hashed_index += 1
    result = hash_object.hexdigest().lower()
    logger.info(
        f"hash_folder_cache: {folder_path}, algorithm: {algorithm}, max_threads: {max_threads}, result: {result},objects: {len(files)}"
    )
    return result


def _decode_bytes_to_str(data: bytes) -> str:
    return data.hex()


def _encode_str_to_bytes(data: str) -> bytes:
    return bytes.fromhex(data)
