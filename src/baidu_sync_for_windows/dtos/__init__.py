from .scan import ScanDTO
from .compress import CompressDTO,EncryptNameCompressDTO
from .verify import VerifyDTO,EncryptNameVerifyDTO
from .backup import BackupDTO,EncryptNameBackupDTO
from .hash import HashDTO
__all__ = [
    "ScanDTO",
    "CompressDTO",
    "VerifyDTO",
    "BackupDTO",
    "HashDTO",
    "EncryptNameCompressDTO",
    "EncryptNameVerifyDTO",
    "EncryptNameBackupDTO"
]