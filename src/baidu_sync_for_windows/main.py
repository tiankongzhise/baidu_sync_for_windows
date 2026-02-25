from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import queue
import threading
from typing import Callable
from baidu_sync_for_windows.service import scan_service,compress_object,verify_object,backup_object,DiskSpaceCoordinator
from baidu_sync_for_windows.repository import default_repository,DefaultRepository
from baidu_sync_for_windows.config import get_config
from baidu_sync_for_windows.dtos import ScanDTO
END_OF_QUEUE = object()
backup_queue = queue.Queue()
def sync_object_producer(scan_result:ScanDTO,repository:DefaultRepository,disk_space_coordinator:DiskSpaceCoordinator):
    compress_result = compress_object(scan_result,disk_space_coordinator)
    repository.save(compress_result)
    verify_result = verify_object(compress_result,disk_space_coordinator)
    repository.save(verify_result)
    print(f"Verify result: {verify_result}")
    backup_queue.put(verify_result)

def sync_object_consumer(repository:DefaultRepository,disk_space_coordinator:DiskSpaceCoordinator):
    while True:
        verify_result = backup_queue.get()
        if verify_result is END_OF_QUEUE:
            print("Received END_OF_QUEUE, terminating consumer thread")
            break
        backup_result = backup_object(verify_result,disk_space_coordinator)
        repository.save(backup_result)
        backup_queue.task_done()


def get_dependency():
    disk_space_coordinator = DiskSpaceCoordinator(
    {
        'compression': 40 * 1024 * 1024 * 1024,
        'verification': 30 * 1024 * 1024 * 1024,
        'backup': 10 * 1024 * 1024 * 1024,
    }
)
    repository = default_repository()
    return disk_space_coordinator,repository

def get_objects():
    config = get_config()
    target_path_list = config.source_path.target_path
    scan_result = scan_service(target_path_list)
    return scan_result

def start_consumer(consumer_worker:Callable,repository:DefaultRepository,disk_space_coordinator:DiskSpaceCoordinator):
    consumer_thread = threading.Thread(target=consumer_worker,args=(repository,disk_space_coordinator))
    consumer_thread.start()
    return consumer_thread

def start_producer(producer_worker:Callable,objects:list[ScanDTO],repository:DefaultRepository,disk_space_coordinator:DiskSpaceCoordinator):
    with ThreadPoolExecutor(max_workers=4) as executor:
        for object in objects:
            executor.submit(producer_worker,object,repository,disk_space_coordinator)

def wait_for_complete(consumer_thread:threading.Thread,consumer_queue:queue.Queue):
    consumer_queue.join()
    consumer_queue.put(END_OF_QUEUE)
    consumer_thread.join()

def main():
    print("Starting program")
    try:
        disk_space_coordinator,repository = get_dependency()
        objects = get_objects()
        consumer_thread = start_consumer(sync_object_consumer,repository,disk_space_coordinator)
        start_producer(sync_object_producer,objects,repository,disk_space_coordinator)
        wait_for_complete(consumer_thread,backup_queue)
        print("Program completed successfully")
    except KeyboardInterrupt:
        print("Keyboard interrupt received, terminating program")
        backup_queue.put(END_OF_QUEUE)
        consumer_thread.join(timeout=5)
        if consumer_thread.is_alive():
            print("Consumer thread is still alive,timeout, terminating program")
            import os
            os._exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        import os
        os._exit(1)

if __name__ == "__main__":
    main()