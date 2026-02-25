
from baidu_sync_for_windows.dtos import ScanDTO,CompressDTO,VerifyDTO,BackupDTO
from baidu_sync_for_windows.exception import RepositoryException
from baidu_sync_for_windows.logger import get_logger
from sqlalchemy import Engine
from typing import overload
from sqlalchemy.orm import Session
from sqlalchemy import text

class MysqlRepository:
    def __init__(self,engine:Engine):
        self.engine = engine
        self.logger = get_logger(bind={'repository_name':'mysql'})
        self._test_connection()
    @overload
    def save(self,data:ScanDTO):
        ...
    @overload
    def save(self,data:CompressDTO):
        ...
    @overload
    def save(self,data:VerifyDTO):
        ...
    @overload
    def save(self,data:BackupDTO):
        ...
    def save(self,data:ScanDTO|CompressDTO|VerifyDTO|BackupDTO):
        match data:
            case ScanDTO():
                self.save(data)
            case CompressDTO():
                self.save(data)
            case VerifyDTO():
                self.save(data)
            case BackupDTO():
                self.save(data)
    def get(self,id:str):
        ...
    def update(self,id:str,data:ScanDTO|CompressDTO|VerifyDTO|BackupDTO):
        ...
    def insert(self,data:ScanDTO|CompressDTO|VerifyDTO|BackupDTO):
        ...
    def execute(self,query:str):
        ...
    def _test_connection(self):
        try:
            with Session(self.engine) as session:
                session.execute(text("SELECT 1"))
                session.commit()
                self.logger.info("Connection test successful")
        except Exception as e:
            self.logger.error(f"Failed to test connection: {e}")
            raise RepositoryException(f"Failed to test connection: {e}")