import time
from contextlib import contextmanager
from baidu_sync_for_windows.models.service import ServiceBase, RecordTypeClass
from baidu_sync_for_windows.repository import get_default_repository
from pathlib import Path


@contextmanager
def benchmark_time(name: str):
    start_time = time.time()
    yield
    end_time = time.time()
    print(f"{name} time: {end_time - start_time} seconds")
    return end_time - start_time

def reset_service_record():
    engine = get_default_repository('scan').engine
    print(f"reset_service_record: {engine}")
    ServiceBase.metadata.drop_all(engine)
    print(f"drop_all: {engine}")
    ServiceBase.metadata.create_all(engine)
    print(f"create_all: {engine}")


def clean_compress_file(source_id: int):
    compress_repository = get_default_repository("compress")
    compress_record = compress_repository.get_record_by_source_id(source_id)
    if compress_record:
        compress_file_path = Path(compress_record.compress_file_path)
        compress_file_path.unlink()

def reset_table(table_record:RecordTypeClass):
    engine = get_default_repository('scan').engine
    table = table_record.__table__
    print(f"table: {table}")
    print('drop talbe please wait...')
    table_record.metadata.drop_all(engine,tables=[table_record.__table__])
    print('drop table success')
    print('create table please wait...')
    table_record.metadata.create_all(engine,tables=[table_record.__table__])
    print('create table success')


