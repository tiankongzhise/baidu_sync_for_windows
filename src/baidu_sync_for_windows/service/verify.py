from baidu_sync_for_windows.dtos import VerifyDTO
from .scheduler import DiskSpaceCoordinator
def verify_object(source_object_id:int,disk_space_coordinator:DiskSpaceCoordinator)->VerifyDTO:
    ...