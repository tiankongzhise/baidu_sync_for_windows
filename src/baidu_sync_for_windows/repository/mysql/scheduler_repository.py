from baidu_sync_for_windows.models.service import DiskSpaceCoordinatorRecord
from baidu_sync_for_windows.dtos import DiskSpaceCoordinatorDTO
from baidu_sync_for_windows.logger import get_logger
from sqlalchemy.orm import Session
from sqlalchemy import Engine
from .default import create_default_engine

class DiskSpaceCoordinatorRepository(object):
    def __init__(self, engine: Engine|None = None):
        self.engine = engine or create_default_engine()
        self.logger = get_logger(bind={'repository_name':'scheduler'})
    
    
    def get_session(self)->Session:
        return Session(self.engine)
    def insert(self, data: DiskSpaceCoordinatorDTO) -> DiskSpaceCoordinatorRecord:
        with self.get_session() as session:
            record = DiskSpaceCoordinatorRecord(**data.model_dump())
            session.add(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record
    def get_record_by_source_id(self, source_id: int,type: str) -> DiskSpaceCoordinatorRecord | None:
        with self.get_session() as session:
            return session.query(DiskSpaceCoordinatorRecord).filter(DiskSpaceCoordinatorRecord.source_id == source_id,DiskSpaceCoordinatorRecord.type == type).first()
    def update(self, data: DiskSpaceCoordinatorDTO) -> DiskSpaceCoordinatorRecord:
        with self.get_session() as session:
            record = session.query(DiskSpaceCoordinatorRecord).filter(DiskSpaceCoordinatorRecord.source_id == data.source_id,DiskSpaceCoordinatorRecord.type == data.type).first()
            if record is None:
                record = self.insert(data)
                return record
            record.disk_space = data.disk_space
            record.status = data.status
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record
    def save(self, data: DiskSpaceCoordinatorDTO) -> DiskSpaceCoordinatorRecord:
        with self.get_session() as session:
            record = session.query(DiskSpaceCoordinatorRecord).filter(DiskSpaceCoordinatorRecord.source_id == data.source_id,DiskSpaceCoordinatorRecord.type == data.type).first()
            if record is None:
                record = self.insert(data)
                return record
            if self.is_equal(record, data):
                session.expunge(record)
                return record
            record = self.update(data)
            return record
    def get_unreleased_record(self) -> list[DiskSpaceCoordinatorRecord]:
        with self.get_session() as session:
            return session.query(DiskSpaceCoordinatorRecord).filter(DiskSpaceCoordinatorRecord.status == "acquire").all()

    def is_equal(self, record: DiskSpaceCoordinatorRecord, data: DiskSpaceCoordinatorDTO) -> bool:
        return record.disk_space == data.disk_space and record.status == data.status and record.type == data.type and record.source_id == data.source_id