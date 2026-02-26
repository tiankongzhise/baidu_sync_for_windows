from baidu_sync_for_windows.dtos import CompressDTO
from .scheduler import DiskSpaceCoordinator
def compress_object(source_object_id:int,disk_space_coordinator:DiskSpaceCoordinator)->CompressDTO:
    ...