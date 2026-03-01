from pydantic import BaseModel,Field,model_validator
from baidu_sync_for_windows.exception import HashServiceException
class HashDTO(BaseModel):
    source_id: int
    md5: str | None = Field(default=None,description="MD5")
    sha1: str | None = Field(default=None,description="SHA1")
    sha256: str | None = Field(default=None,description="SHA256")
    fast_hash: str | None = Field(default=None,description="Fast Hash")

    @model_validator(mode='after')
    def validate_hash_fields(self) -> 'HashDTO':
        # 收集三大哈希字段的值
        main_hashes = [self.md5, self.sha1, self.sha256]
        # 判断三大哈希字段是否全不为 None
        all_main_hashes_present = all(hash_val is not None for hash_val in main_hashes)
        # 判断三大哈希字段是否全为 None
        all_main_hashes_none = all(hash_val is None for hash_val in main_hashes)

        # 规则1：md5、sha1、sha256 同时存在时，fast_hash 必须为 None
        if all_main_hashes_present:
            if self.fast_hash is not None:
                raise HashServiceException(
                    "When md5, sha1, sha256 are all provided, fast_hash must be None"
                )
        # 规则2：md5、sha1、sha256 全为 None 时，fast_hash 不能为 None
        elif all_main_hashes_none:
            if self.fast_hash is None:
                raise HashServiceException(
                    "When md5, sha1, sha256 are all None, fast_hash must be provided"
                )
        # 规则3：不允许部分主哈希字段存在的情况
        else:
            raise HashServiceException(
                "md5, sha1, sha256 must all be present or all be None"
            )
        return self