from baidu_sync_for_windows.models.oauth import OauthRecord
from baidu_sync_for_windows.dtos import OauthDTO
from baidu_sync_for_windows.logger import get_logger
from baidu_sync_for_windows.config import get_config
from sqlalchemy.orm import Session
from sqlalchemy import create_engine,Engine

class OauthRepository(object):
    def __init__(self, engine: Engine|None = None):
        self.engine = engine or self._default_engine()
        self.logger = get_logger(bind={'repository_name':'oauth'})
    
    def _default_engine(self)->Engine:
        config = get_config()
        database = config.database.database_config.database
        connector = config.database.database_config.connector
        user = config.database.database_secret_info.db_user.get_secret_value()
        password = config.database.database_secret_info.db_password.get_secret_value()
        host = config.database.database_secret_info.db_host.get_secret_value()
        port = config.database.database_secret_info.db_port
        name = 'object_backup_test'
        engine_url = f"{database}+{connector}://{user}:{password}@{host}:{port}/{name}"
        engine_params = config.database.database_config.model_dump()
        engine_params.pop("database")
        engine_params.pop("connector")
        return create_engine(engine_url,**engine_params)
    
    def get_session(self)->Session:
        return Session(self.engine)
    def insert(self, data: OauthDTO) -> OauthRecord:
        with self.get_session() as session:
            record = OauthRecord(**data.model_dump())
            session.add(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record
    def get_record_by_platform(self, platform: str) -> OauthRecord | None:
        with self.get_session() as session:
            return session.query(OauthRecord).filter(OauthRecord.platform == platform).first()
    def update(self, data: OauthDTO) -> OauthRecord:
        with self.get_session() as session:
            record = session.query(OauthRecord).filter(OauthRecord.platform == data.platform).first()
            if record is None:
                record = self.insert(data)
                return record
            record.auth_info = data.auth_info.model_dump()
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record
    def save(self, data: OauthDTO) -> OauthRecord:
        with self.get_session() as session:
            record = session.query(OauthRecord).filter(OauthRecord.platform == data.platform).first()
            if record is None:
                record = self.insert(data)
                return record
            if self.is_equal(record, data):
                session.expunge(record)
                return record
            record = self.update(data)
            return record
    
    def is_equal(self, record: OauthRecord, data: OauthDTO) -> bool:
        return record.auth_info == data.auth_info.model_dump()