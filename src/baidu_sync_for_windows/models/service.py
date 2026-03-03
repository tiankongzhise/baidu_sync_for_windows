from .base import Base
from sqlalchemy.orm import Mapped, mapped_column,relationship
from sqlalchemy import  MetaData,UniqueConstraint,String,JSON,Integer,ForeignKey,BigInteger
from typing import Literal
class ServiceBase(Base):
    __abstract__ = True
    metadata = MetaData()
class SourceRecord(ServiceBase):
    __tablename__ = "source_record"
    drive_letter: Mapped[str] = mapped_column(String(255))
    target_object_path: Mapped[str] = mapped_column(String(255))
    target_object_name: Mapped[str] = mapped_column(String(255))
    target_object_type: Mapped[str] = mapped_column(String(255))
    target_object_size: Mapped[int] = mapped_column(BigInteger)
    target_object_items_count: Mapped[int] = mapped_column(Integer)
    target_object_items: Mapped[dict[str,int]] = mapped_column(JSON)
    process_type: Mapped[Literal['auto','manual']] = mapped_column(String(10))
    __table_args__ = (
        UniqueConstraint("drive_letter", "target_object_path",name="uix_drive_letter_target_object_path"),
    )
    def __str__(self) -> str:
        return (f"SourceObjectRecord(id={self.id}, drive_letter={self.drive_letter}, target_object_path={self.target_object_path}, target_object_name={self.target_object_name}, target_object_type={self.target_object_type}, target_object_size={self.target_object_size}, target_object_items_count={self.target_object_items_count}, target_object_items={self.target_object_items}, process_type={self.process_type}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")

class HashRecord(ServiceBase):
    __tablename__ = "hash_record"
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_record.id"))
    source: Mapped["SourceRecord"] = relationship("SourceRecord", backref="hash_records", init=False)
    md5: Mapped[str] = mapped_column(String(32),nullable=True)
    sha1: Mapped[str] = mapped_column(String(40),nullable=True)
    sha256: Mapped[str] = mapped_column(String(64),nullable=True)
    fast_hash: Mapped[str] = mapped_column(String(64),nullable=True)
    __table_args__ = (
        UniqueConstraint("source_id",name="uix_source_id"),
    )
    def __str__(self) -> str:
        return (f"HashRecord(id={self.id}, source_id={self.source_id}, md5={self.md5}, sha1={self.sha1}, sha256={self.sha256}, fast_hash={self.fast_hash}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class CompressRecord(ServiceBase):
    __tablename__ = "compress_record"
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_record.id"))
    source: Mapped["SourceRecord"] = relationship("SourceRecord", backref="compress_records", init=False)
    compress_file_path: Mapped[str] = mapped_column(String(255))
    __table_args__ = (
            UniqueConstraint("source_id",name="uix_source_id"),
    )
    def __str__(self) -> str:
            return (f"CompressRecord(id={self.id}, source_id={self.source_id}, compress_file_path={self.compress_file_path}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class EncryptNameCompressRecord(ServiceBase):
    __tablename__ = "encrypt_name_compress_record"
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_record.id"))
    source: Mapped["SourceRecord"] = relationship("SourceRecord", backref="encrypt_name_compress_records", init=False)
    encrypt_name_compress_object_path: Mapped[str] = mapped_column(String(255))
    __table_args__ = (
        UniqueConstraint("source_id",name="uix_source_id"),
    )
    def __str__(self) -> str:
        return (f"EncryptNameCompressRecord(id={self.id}, source_id={self.source_id}, encrypt_name_compress_object_path={self.encrypt_name_compress_object_path}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class VerifyRecord(ServiceBase):
    __tablename__ = "verify_record"
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_record.id"))
    source: Mapped["SourceRecord"] = relationship("SourceRecord", backref="verify_records", init=False)
    verify_compress_file_path: Mapped[str] = mapped_column(String(255))
    md5: Mapped[str] = mapped_column(String(32),nullable=True)
    sha1: Mapped[str] = mapped_column(String(40),nullable=True)
    sha256: Mapped[str] = mapped_column(String(64),nullable=True)
    fast_hash: Mapped[str] = mapped_column(String(64),nullable=True)
    verify_result: Mapped[Literal['success','failed']] = mapped_column(String(10))
    __table_args__ = (
        UniqueConstraint("source_id",name="uix_source_id"),
    )
    def __str__(self) -> str:
        return (f"VerifyRecord(id={self.id}, source_id={self.source_id}, verify_compress_file_path={self.verify_compress_file_path}, md5={self.md5}, sha1={self.sha1}, sha256={self.sha256}, fast_hash={self.fast_hash}, verify_result={self.verify_result}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class EncryptNameVerifyRecord(ServiceBase):
    __tablename__ = "encrypt_name_verify_record"
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_record.id"))
    source: Mapped["SourceRecord"] = relationship("SourceRecord", backref="encrypt_name_verify_records", init=False)
    encrypt_name_verify_object_path: Mapped[str] = mapped_column(String(255))
    verify_result: Mapped[Literal['success','failed']] = mapped_column(String(10))
    __table_args__ = (
            UniqueConstraint("source_id",name="uix_source_id"),
    )
    def __str__(self) -> str:
        return (f"EncryptNameVerifyRecord(id={self.id}, source_id={self.source_id}, encrypt_name_verify_object_path={self.encrypt_name_verify_object_path}, verify_result={self.verify_result}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class BackupRecord(ServiceBase):
    __tablename__ = "backup_record"
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_record.id"))
    source: Mapped["SourceRecord"] = relationship("SourceRecord", backref="backup_records", init=False)
    backup_object_path: Mapped[str] = mapped_column(String(255))
    remote_file_name: Mapped[str] = mapped_column(String(255))
    remote_file_hash: Mapped[str] = mapped_column(String(32))
    __table_args__ = (
        UniqueConstraint("source_id",name="uix_source_id"),
        UniqueConstraint("remote_file_name",name="uix_remote_file_name"),
    )
    def __str__(self) -> str:
        return (f"BackupObjectRecord(id={self.id}, source_id={self.source_id}, backup_object_path={self.backup_object_path}, remote_file_name={self.remote_file_name}, remote_file_hash={self.remote_file_hash}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class EncryptNameBackupRecord(ServiceBase):
    __tablename__ = "encrypt_name_backup_record"
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_record.id"))
    source: Mapped["SourceRecord"] = relationship("SourceRecord", backref="encrypt_name_backup_records", init=False)
    encrypt_name_backup_object_path: Mapped[str] = mapped_column(String(255))
    remote_file_name: Mapped[str] = mapped_column(String(255))
    remote_file_hash: Mapped[str] = mapped_column(String(32))
    __table_args__ = (
        UniqueConstraint("source_id",name="uix_source_id"),
        UniqueConstraint("remote_file_name",name="uix_remote_file_name"),
    )
    def __str__(self) -> str:
        return (f"EncryptNameBackupObjectRecord(id={self.id}, source_id={self.source_id}, encrypt_name_backup_object_path={self.encrypt_name_backup_object_path}, remote_file_name={self.remote_file_name}, remote_file_hash={self.remote_file_hash}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
