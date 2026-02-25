from baidu_sync_for_windows.dtos import CompressDTO,VerifyDTO
from .scheduler import Scheduler
def verify_object(compress_result:CompressDTO,scheduler:Scheduler)->VerifyDTO:
    ...