from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import queue
import threading
from baidu_sync_for_windows.service import scan_object,compress_object,verify_object,backup_object,DiskSpaceCoordinator
from baidu_sync_for_windows.repository import default_repository,DefaultRepository
END_OF_QUEUE = object()
backup_queue = queue.Queue()
def sync_object_producer(object_path:str|Path,repository:DefaultRepository,disk_space_coordinator:DiskSpaceCoordinator):
    scan_result = scan_object(object_path)
    repository.save(scan_result)
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


def main():
    print("Starting program")
    try:
        disk_space_coordinator = DiskSpaceCoordinator(
            {
                'compression': 40 * 1024 * 1024 * 1024,
                'verification': 30 * 1024 * 1024 * 1024,
                'backup': 10 * 1024 * 1024 * 1024,
            }
        )
        repository = default_repository()
        objects = [...]
        consumer_thread = threading.Thread(target=sync_object_consumer,args=(repository,disk_space_coordinator))
        consumer_thread.start()
        with ThreadPoolExecutor(max_workers=4) as executor:
            for object in objects:
                executor.submit(sync_object_producer,object,repository,disk_space_coordinator)
        backup_queue.join()
        backup_queue.put(END_OF_QUEUE)
        print("Waiting for consumer thread to finish")
        consumer_thread.join()
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