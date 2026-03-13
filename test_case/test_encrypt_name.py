from baidu_sync_for_windows.service import encrypt_name_compress_service
from baidu_sync_for_windows.service import DiskSpaceCoordinator



def test_encrypt_name_compress_service():
    source_id = range(19,26)
    disk_space_coordinator = DiskSpaceCoordinator(quotas={"compress": 1024**3, "verification": 1024**3})
    for id in source_id:
        result = encrypt_name_compress_service(id, disk_space_coordinator)
        print(result)

if __name__ == "__main__":
    test_encrypt_name_compress_service()