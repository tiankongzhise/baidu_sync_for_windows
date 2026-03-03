import time
from contextlib import contextmanager
from baidu_sync_for_windows.models.service import ServiceBase
from baidu_sync_for_windows.repository import get_default_repository
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