from dtos import VerifyDTO,BackupDTO
from .scheduler import Scheduler
def backup_object(verify_result:VerifyDTO,scheduler:Scheduler)->BackupDTO:
    ...
