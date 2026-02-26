from baidu_sync_for_windows.dtos import BackupDTO
from .scheduler import DiskSpaceCoordinator
def backup_object(source_object_id:int,disk_space_coordinator:DiskSpaceCoordinator)->BackupDTO:
    ...
