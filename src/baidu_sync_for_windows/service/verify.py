from dtos import CompressDTO,VerifyDTO
from .scheduler import Scheduler
def verify_object(compress_result:CompressDTO,scheduler:Scheduler)->VerifyDTO:
    ...