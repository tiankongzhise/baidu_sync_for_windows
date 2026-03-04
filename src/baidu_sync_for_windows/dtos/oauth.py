from pydantic import BaseModel, Field, SecretStr,model_validator
from baidu_sync_for_windows.exception import AuthorizationException
class OauthInfo(BaseModel):
    access_token: SecretStr
    refresh_token: SecretStr
    app_key: SecretStr
    app_secret: SecretStr
    expires_at: int

    @model_validator(mode='after')
    def validate_expires_at(self) -> 'OauthInfo':
        # 如果expires_at为秒，转化为纳秒存储
        if len(str(self.expires_at)) == 10:
            self.expires_at *= 1_000_000_000
        elif len(str(self.expires_at)) == 13:
            self.expires_at *= 1_000_000
        elif len(str(self.expires_at)) == 19:
            pass
        else:
            raise AuthorizationException(
                "expires_at格式错误"
            )
        return self

class OauthDTO(BaseModel):
    platform: str = Field(..., description="平台")
    auth_info: OauthInfo = Field(..., description="认证信息")
    @property
    def access_token(self) -> SecretStr:
        return self.auth_info.access_token
    @property
    def refresh_token(self) -> SecretStr:
        return self.auth_info.refresh_token
    @property
    def app_key(self) -> SecretStr:
        return self.auth_info.app_key
    @property
    def app_secret(self) -> SecretStr:
        return self.auth_info.app_secret
    @property
    def decrypt_auth_info(self) -> dict[str, str|int]:
        return {
            "access_token": self.access_token.get_secret_value(),
            "refresh_token": self.refresh_token.get_secret_value(),
            "app_key": self.app_key.get_secret_value(),
            "app_secret": self.app_secret.get_secret_value(),
            "expires_at": self.auth_info.expires_at
        }
    @property
    def decrypt_access_token(self) -> str:
        return self.access_token.get_secret_value()
    @property
    def decrypt_refresh_token(self) -> str:
        return self.refresh_token.get_secret_value()
    @property
    def decrypt_app_key(self) -> str:
        return self.app_key.get_secret_value()
    @property
    def decrypt_app_secret(self) -> str:
        return self.app_secret.get_secret_value()