from .scan import ScanDTO
from .compress import CompressDTO,EncryptNameCompressDTO
from .verify import VerifyDTO,EncryptNameVerifyDTO
from .backup import BackupDTO,EncryptNameBackupDTO,BaiduPanRefreshResponse
from .hash import HashDTO
from .oauth import OauthDTO,OauthInfo
from .scheduler import DiskSpaceCoordinatorDTO
__all__ = [
    "ScanDTO",
    "CompressDTO",
    "VerifyDTO",
    "BackupDTO",
    "HashDTO",
    "EncryptNameCompressDTO",
    "EncryptNameVerifyDTO",
    "EncryptNameBackupDTO",
    "BaiduPanRefreshResponse",
    "OauthDTO",
    "OauthInfo",
    "DiskSpaceCoordinatorDTO"
]