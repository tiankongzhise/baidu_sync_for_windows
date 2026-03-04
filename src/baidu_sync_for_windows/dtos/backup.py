from pydantic import BaseModel, Field, SecretStr
class BackupDTO(BaseModel):
    source_id: int = Field(..., description="源ID")
    backup_object_path: str = Field(..., description="备份对象路径")
    remote_file_name: str = Field(..., description="远程文件名")
    remote_file_hash: str = Field(..., description="远程文件哈希")

class EncryptNameBackupDTO(BaseModel):
    source_id: int = Field(..., description="源ID")
    origin_file_name: str = Field(..., description="原始文件名")
    encrypt_file_name: str = Field(..., description="加密文件名")
    backup_object_path: str = Field(..., description="备份对象路径")
    remote_file_name: str = Field(..., description="远程文件名")
    remote_file_hash: str = Field(..., description="远程文件哈希")

class BaiduPanRefreshResponse(BaseModel):
    access_token: SecretStr = Field(..., description="访问令牌")
    refresh_token: SecretStr = Field(..., description="刷新令牌")
    expires_in: int = Field(..., description="过期时间（秒）")