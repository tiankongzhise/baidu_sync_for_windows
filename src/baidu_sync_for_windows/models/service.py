from .base import Base
from sqlalchemy.orm import Mapped, mapped_column,relationship
from sqlalchemy import  MetaData,UniqueConstraint,String,JSON,Integer,ForeignKey
from typing import Literal
class ServiceBase(Base):
    __abstract__ = True
    metadata = MetaData()
class SourceObjectRecord(ServiceBase):
    __tablename__ = "source_object_record"
    drive_letter: Mapped[str] = mapped_column(String(255))
    target_object_path: Mapped[str] = mapped_column(String(255))
    target_object_name: Mapped[str] = mapped_column(String(255))
    target_object_type: Mapped[str] = mapped_column(String(255))
    target_object_size: Mapped[int] = mapped_column(Integer)
    target_object_items_count: Mapped[int] = mapped_column(Integer)
    target_object_items: Mapped[dict[str,int]] = mapped_column(JSON)
    process_type: Mapped[Literal['auto','manual']] = mapped_column(String(10))
    __table_args__ = (
        UniqueConstraint("drive_letter", "target_object_path",name="uix_drive_letter_target_object_path"),
    )
    def __str__(self) -> str:
        return (f"SourceObjectRecord(id={self.id}, drive_letter={self.drive_letter}, target_object_path={self.target_object_path}, target_object_name={self.target_object_name}, target_object_type={self.target_object_type}, target_object_size={self.target_object_size}, target_object_items_count={self.target_object_items_count}, target_object_items={self.target_object_items}, process_type={self.process_type}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")

class ObjectHashRecord(ServiceBase):
    __tablename__ = "object_hash_record"
    source_object_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_object_record.id"))
    source_object: Mapped["SourceObjectRecord"] = relationship("SourceObjectRecord", backref="object_hash_records")
    md5: Mapped[str] = mapped_column(String(32))
    sha1: Mapped[str] = mapped_column(String(40))
    sha256: Mapped[str] = mapped_column(String(64))
    fast_hash: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        UniqueConstraint("source_object_id",name="uix_source_object_id"),
    )
    def __str__(self) -> str:
        return (f"ObjectHashRecord(id={self.id}, source_object_id={self.source_object_id}, md5={self.md5}, sha1={self.sha1}, sha256={self.sha256}, fast_hash={self.fast_hash}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class ObjectCompressRecord(ServiceBase):
    __tablename__ = "compress_object_record"
    source_object_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_object_record.id"))
    source_object: Mapped["SourceObjectRecord"] = relationship("SourceObjectRecord", backref="object_compress_records")
    compress_object_path: Mapped[str] = mapped_column(String(255))
    __table_args__ = (
        UniqueConstraint("source_object_id",name="uix_source_object_id"),
    )
    def __str__(self) -> str:
        return (f"CompressObjectRecord(id={self.id}, source_object_id={self.source_object_id}, compress_object_path={self.compress_object_path}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class ObjectEncryptNameCompressRecord(ServiceBase):
    __tablename__ = "encrypt_name_compress_object_record"
    source_object_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_object_record.id"))
    source_object: Mapped["SourceObjectRecord"] = relationship("SourceObjectRecord", backref="object_encrypt_name_compress_records")
    encrypt_name_compress_object_path: Mapped[str] = mapped_column(String(255))
    __table_args__ = (
        UniqueConstraint("source_object_id",name="uix_source_object_id"),
    )
    def __str__(self) -> str:
        return (f"EncryptNameCompressObjectRecord(id={self.id}, source_object_id={self.source_object_id}, encrypt_name_compress_object_path={self.encrypt_name_compress_object_path}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class ObjectVerifyRecord(ServiceBase):
    __tablename__ = "verify_object_record"
    source_object_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_object_record.id"))
    source_object: Mapped["SourceObjectRecord"] = relationship("SourceObjectRecord", backref="object_verify_records")
    verify_object_path: Mapped[str] = mapped_column(String(255))
    __table_args__ = (
        UniqueConstraint("source_object_id",name="uix_source_object_id"),
    )
    def __str__(self) -> str:
        return (f"VerifyObjectRecord(id={self.id}, source_object_id={self.source_object_id}, verify_object_path={self.verify_object_path}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class ObjectEncryptNameVerifyRecord(ServiceBase):
    __tablename__ = "encrypt_name_verify_object_record"
    source_object_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_object_record.id"))
    source_object: Mapped["SourceObjectRecord"] = relationship("SourceObjectRecord", backref="object_encrypt_name_verify_records")
    encrypt_name_verify_object_path: Mapped[str] = mapped_column(String(255))
    __table_args__ = (
        UniqueConstraint("source_object_id",name="uix_source_object_id"),
    )
    def __str__(self) -> str:
        return (f"EncryptNameVerifyObjectRecord(id={self.id}, source_object_id={self.source_object_id}, encrypt_name_verify_object_path={self.encrypt_name_verify_object_path}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class ObjectBackupRecord(ServiceBase):
    __tablename__ = "backup_object_record"
    source_object_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_object_record.id"))
    source_object: Mapped["SourceObjectRecord"] = relationship("SourceObjectRecord", backref="object_backup_records")
    backup_object_path: Mapped[str] = mapped_column(String(255))
    backup_object_hash: Mapped[str] = mapped_column(String(32))
    __table_args__ = (
        UniqueConstraint("source_object_id",name="uix_source_object_id"),
        UniqueConstraint("backup_object_hash",name="uix_backup_object_hash"),
    )
    def __str__(self) -> str:
        return (f"BackupObjectRecord(id={self.id}, source_object_id={self.source_object_id}, backup_object_path={self.backup_object_path}, backup_object_hash={self.backup_object_hash}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
class ObjectEncryptNameBackupRecord(ServiceBase):
    __tablename__ = "encrypt_name_backup_object_record"
    source_object_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_object_record.id"))
    source_object: Mapped["SourceObjectRecord"] = relationship("SourceObjectRecord", backref="object_encrypt_name_backup_records")
    encrypt_name_backup_object_path: Mapped[str] = mapped_column(String(255))
    encrypt_name_backup_object_hash: Mapped[str] = mapped_column(String(32))
    __table_args__ = (
        UniqueConstraint("source_object_id",name="uix_source_object_id"),
    )
    def __str__(self) -> str:
        return (f"EncryptNameBackupObjectRecord(id={self.id}, source_object_id={self.source_object_id}, encrypt_name_backup_object_path={self.encrypt_name_backup_object_path}, encrypt_name_backup_object_hash={self.encrypt_name_backup_object_hash}, created_at={self.created_time_to_local_time}, updated_at={self.updated_time_to_local_time}, latested_at={self.latested_time_to_local_time})")
