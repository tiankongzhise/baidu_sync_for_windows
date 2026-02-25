from .base import EnvBaseSettings
from pydantic import Field, SecretStr
class BaiduPanOAuthSettings(EnvBaseSettings):
    baidu_pan_app_key: SecretStr = Field(..., description="百度云盘应用密钥")
    baidu_pan_app_secret: SecretStr = Field(..., description="百度云盘应用密钥")
    baidu_pan_access_token: SecretStr = Field(..., description="百度云盘访问令牌")
    baidu_pan_refresh_token: SecretStr = Field(..., description="百度云盘刷新令牌")
    @property
    def app_key(self) -> str:
        return self.baidu_pan_app_key.get_secret_value()
    @property
    def app_secret(self) -> str:
        return self.baidu_pan_app_secret.get_secret_value()
    @property
    def access_token(self) -> str:
        return self.baidu_pan_access_token.get_secret_value()
    @property
    def refresh_token(self) -> str:
        return self.baidu_pan_refresh_token.get_secret_value()
