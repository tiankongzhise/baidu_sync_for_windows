from baidu_sync_for_windows.dtos import VerifyDTO,BackupDTO
from .scheduler import Scheduler
def backup_object(verify_result:VerifyDTO,scheduler:Scheduler)->BackupDTO:
    ...
