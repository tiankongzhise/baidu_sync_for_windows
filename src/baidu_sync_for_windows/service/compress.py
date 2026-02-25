from baidu_sync_for_windows.dtos import ScanDTO,CompressDTO
from .scheduler import Scheduler
def compress_object(scan_result:ScanDTO,scheduler:Scheduler)->CompressDTO:
    ...