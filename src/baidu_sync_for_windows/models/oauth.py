
from sqlalchemy.orm import   Mapped, mapped_column
from sqlalchemy import  MetaData,UniqueConstraint,String,JSON
from datetime import datetime
from typing import cast
from .base import Base


class OauthBase(Base):
    __abstract__=True
    metadata = MetaData()
    


class OauthRecord(OauthBase):
    __tablename__ = 'oauth_record'
    platform:Mapped[str] = mapped_column(String(32))
    auth_info:Mapped[dict[str, str|int]] = mapped_column(JSON)

    @property
    def expires_at_local_time(self):
        expires_at:int = cast(int, self.auth_info['expires_at'])
        return datetime.fromtimestamp(expires_at / 1_000_000_000)
    @classmethod
    def _encrypt_secret_info(cls,secret_info:str):
        return f'{secret_info[:5]}******{secret_info[-5:]}'
    @property
    def encrypt_access_token(self):
        return self._encrypt_secret_info(cast(str, self.auth_info['access_token']))
    @property
    def encrpt_refresh_token(self):
        return self._encrypt_secret_info(cast(str, self.auth_info['refresh_token']))
    
    @property
    def encrpt_app_key(self):
        return self._encrypt_secret_info(cast(str, self.auth_info['app_key']))

    @property
    def encrpt_app_secret(self):
        return self._encrypt_secret_info(cast(str, self.auth_info['app_secret']))

    __table_args__ = (
        UniqueConstraint(platform,name="uix_platform"),
    )
    def __str__(self) -> str:
        return (f"OauthRecord(id={self.id}, platform={self.platform},expires_at_local_time = {self.expires_at_local_time}, access_token={self.encrypt_access_token}, refresh_token={self.encrpt_refresh_token}, app_key={self.encrpt_app_key}, app_secret={self.encrpt_app_secret}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")

