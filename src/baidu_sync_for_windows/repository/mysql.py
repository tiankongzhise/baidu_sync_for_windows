from sqlalchemy import Engine
from dtos import ScanDTO,CompressDTO,VerifyDTO,BackupDTO
from typing import overload


class MysqlRepository:
    def __init__(self,engine:Engine):
        self.engine = engine
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
