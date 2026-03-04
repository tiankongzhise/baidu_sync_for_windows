import traceback
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Callable
from baidu_sync_for_windows.service import scan_service,compress_service,verify_service,backup_service,DiskSpaceCoordinator,hash_service
from baidu_sync_for_windows.repository import get_default_repository
from baidu_sync_for_windows.config import get_config
from baidu_sync_for_windows.dtos import ScanDTO
from baidu_sync_for_windows.logger import get_logger
logger = get_logger(bind={'module_name':'main'})
def sync_object_producer(source_object_id:int,disk_space_coordinator:DiskSpaceCoordinator):
    _,hash_result = hash_service(source_object_id)
    if hash_result:
        hash_repository = get_default_repository('hash')
        hash_repository.save(hash_result)
    _,compress_result = compress_service(source_object_id,disk_space_coordinator)
    if compress_result:
        compress_repository = get_default_repository('compress')
        compress_repository.save(compress_result)
    _,verify_result = verify_service(source_object_id,disk_space_coordinator)
    if verify_result:
        verify_repository = get_default_repository('verify')
        verify_repository.save(verify_result)

def sync_object_consumer():
    try:
        is_backup_ids_changed = True
        backup_ids = []
        while is_backup_ids_changed:
            repository = get_default_repository('backup')
            source_ids_to_backup = repository.get_source_ids_to_backup()
            source_ids = [source_id for source_id in source_ids_to_backup if source_id not in backup_ids]
            if not source_ids:
                is_backup_ids_changed = False
            for source_object_id in source_ids:
                backup_ids.append(source_object_id)
                _,backup_result = backup_service(source_object_id)
                if backup_result:
                    backup_repository = get_default_repository('backup')
                    backup_repository.save(backup_result)
    except KeyboardInterrupt:
        logger.log("SERVICE_INFO","Keyboard interrupt received, terminating program")
        is_backup_ids_changed = False


    except Exception as e:
        logger.error(f"save backup_result failed: {e}")
        traceback.print_exc()


def get_dependency():
    disk_space_coordinator = DiskSpaceCoordinator(
    {
        'compress': 40 * 1024 * 1024 * 1024,
        'verify': 30 * 1024 * 1024 * 1024,
    }
    )
    logger.info("get_dependency success")
    return disk_space_coordinator

def get_objects():
    config = get_config()
    target_path_list = config.source_path.target_path
    scan_result = scan_service(target_path_list)
    logger.info("get_objects success")
    return scan_result

def get_source_object_ids(objects:list[ScanDTO])->list[int]:
    source_object_ids = []
    scan_repository = get_default_repository('scan')
    for object in objects:
        record = scan_repository.save(object)
        source_object_ids.append(record.id)
    return source_object_ids

def start_consumer(consumer_worker:Callable):
    consumer_thread = threading.Thread(target=consumer_worker)
    consumer_thread.start()
    return consumer_thread

def start_producer(producer_worker:Callable,source_object_ids:list[int],disk_space_coordinator:DiskSpaceCoordinator):
    """提交生产者任务并等待全部完成；任一任务抛异常会在此处抛出，避免异常被线程池吞掉。"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(producer_worker, source_object_id, disk_space_coordinator)
            for source_object_id in source_object_ids
        ]
        for future in futures:
            future.result()  # 使工作线程中的异常抛到主线程，否则 save() 失败会静默

def wait_for_complete(consumer_thread:threading.Thread):
    consumer_thread.join()

def main():
    print("Starting program")
    consumer_thread = None
    try:
        disk_space_coordinator = get_dependency()
        objects = get_objects()
        source_object_ids = get_source_object_ids(objects)
        consumer_thread = start_consumer(sync_object_consumer)
        start_producer(sync_object_producer,source_object_ids,disk_space_coordinator)
        wait_for_complete(consumer_thread)
        print("Program completed successfully")
    except KeyboardInterrupt:
        print("Keyboard interrupt received, terminating program")
        if consumer_thread:
            consumer_thread.join(timeout=5)
        if consumer_thread and consumer_thread.is_alive():
            print("Consumer thread is still alive,timeout, terminating program")
            import os
            os._exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        import os
        os._exit(1)

if __name__ == "__main__":
    main()