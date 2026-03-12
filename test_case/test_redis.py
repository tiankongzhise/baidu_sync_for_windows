
import random
import pathlib
import json
from redis import Redis,asyncio as async_redis
import timeit
from concurrent.futures import ThreadPoolExecutor,as_completed
import asyncio
from baidu_sync_for_windows.utils import benchmark_time
from baidu_sync_for_windows.cache.redis_cache import RedisCacheService
def create_random_data():
    redis_test_data = pathlib.Path('redis_test_data.json')
    if redis_test_data.exists():
        return 
    data = {}
    for _ in range(10000):
        data[f'test_{random.randint(1, 1000000)}'] = f'value_{random.randint(1, 1000000)}'
    with open(redis_test_data, 'w') as f:
        json.dump(data, f)
    print(f'create {len(data.keys())} data success')
    return redis_test_data
def get_random_data()->dict[str, str]|None:
    redis_test_data = pathlib.Path('redis_test_data.json')
    if not redis_test_data.exists():
        return None
    with open(redis_test_data, 'r') as f:
        data = json.load(f)
    print(f'get {len(data.keys())} data success')
    return data

def set_random_data(r: Redis, data: dict[str, str]):
    print(f'set {len(data.keys())} data start')
    # pipe=r.pipeline()
    pipe =r
    for key, value in data.items():
        pipe.set(key, value)
        print(f'set {key} {value} success', end='\r')
    # pipe.execute()
    print(f'set {len(data.keys())} data end')
    for key, value in data.items():
        if r.get(key) != value:
            raise Exception(f'set {key} {value} failed')
        print(f'get {key} {value} success', end='\r')
    print(f'set {len(data)} data success')

def test_set_random_data():
    r = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print('create random data failed')
        return
    set_random_data(r, data)

def test_redis_is_append():
    r = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print('create random data failed')
        return
    for key, value in data.items():
        if r.get(key) != value:
            raise Exception(f'append {key} {value} failed')
        print(f'get {key} {value} success', end='\r')
    print(f'append {len(data.keys())} data success')


def set_worker(r: Redis, data: tuple[str, str]):
    r.set(data[0], data[1])
    return data[0]
def get_worker(r: Redis, data: tuple[str, str]):
    return data[0],r.get(data[0]),data[1]
def test_muti_redis(max_workers:int=4):
    print(f'test_muti_redis with {max_workers} workers')
    r = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    
    if data is None:
        print("create random data failed")
        return
    data = tuple(data.items())
    tasks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [executor.submit(set_worker, r, data) for data in data]
        for task in as_completed(tasks):
            print(f"set {task.result()} success", end="\r")
    print(f"set {len(data)} data success")
    end_list = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [executor.submit(get_worker, r, data) for data in data]
        for task in as_completed(tasks):
            data_key,data_get,data_expected = task.result()
            if data_get != data_expected:
                raise Exception(f"get {data_key} {data_expected} failed")
            end_list.append(data_key)
            print(f"get {data_key} {data_get} success", end="\r")
    print('\n')
    print(f"get {len(end_list)} data success")

async def set_async_redis_worker(r: async_redis.Redis, data: tuple[str, str],semaphore:asyncio.Semaphore):
    async with semaphore:
        await r.set(data[0], data[1])
        return data[0]
async def get_async_redis_worker(r: async_redis.Redis, data: tuple[str, str],semaphore:asyncio.Semaphore):
    async with semaphore:
        return data[0],await r.get(data[0]),data[1]

async def test_async_redis_worker():
    r = await async_redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    data = tuple(data.items())
    semaphore = asyncio.Semaphore(30)
    tasks = [set_async_redis_worker(r, data, semaphore) for data in data]
    completed_tasks = 0
    for task in asyncio.as_completed(tasks):
        result = await task
        completed_tasks += 1
        print(f"set {completed_tasks} success, result: {result}", end="\r")
    print('\n')
    print(f"set {completed_tasks} data success")
    tasks = [get_async_redis_worker(r, data, semaphore) for data in data]
    completed_tasks = 0
    for task in asyncio.as_completed(tasks):
        key,result,expected = await task
        completed_tasks += 1
        if result != expected:
            raise Exception(f"get {key} {expected} failed")
        print(f"get {key} {result} {expected} success", end="\r")
    print('\n')
    print(f"get {completed_tasks} data success")

def test_async_redis():
    asyncio.run(test_async_redis_worker())

def test_redis_pipeline():
    r = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    print(f'test_redis_pipeline with {len(data.keys())} data')
    pipeline = r.pipeline()
    for key, value in data.items():
        pipeline.set(key, value)
    pipeline.execute()
    for key, value in data.items():
        pipeline.get(key)
    results = pipeline.execute()
    print(f'pipeline execute results: {len(results)}')


def test_redis_set():
    r = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    print(f'test_redis_set with {len(data.keys())} data')
    for key, value in data.items():
        r.set(key, value)
        print(f"set {key} {value} success", end="\r")
    print('\n')
    print(f"set {len(data.keys())} data success")
def test_redis_get():
    r = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    print(f'test_redis_get with {len(data.keys())} data')
    for key, value in data.items():
        if r.get(key) != value:
            raise Exception(f"get {key} {value} failed")
        print(f"get {key} {value} success", end="\r")
    print('\n')
    print(f"get {len(data.keys())} data success")

def test_redis_set_and_get():
    set_time = timeit.timeit(test_redis_set, number=1)
    get_time = timeit.timeit(test_redis_get, number=1)
    print(f'test_redis_set time: {set_time} seconds')
    print(f'test_redis_get time: {get_time} seconds')

def test_redis_set_multi_thread(max_workers:int=4):
    r = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    print(f'test_redis_set_multi_thread with {len(data.keys())} data')
    tuple_data = tuple(data.items())
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [executor.submit(set_worker, r, data) for data in tuple_data]
        for task in as_completed(tasks):
            print(f"set {task.result()} success", end="\r")
    print('\n')
    print(f"set {len(tuple_data)} data success")

def test_redis_get_multi_thread(max_workers:int=4):
    r = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    print(f'test_redis_get_multi_thread with {len(data.keys())} data')
    tuple_data = tuple(data.items())
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [executor.submit(get_worker, r, data) for data in tuple_data]
        for task in as_completed(tasks):
            print(f"get {task.result()} success", end="\r")
    print('\n')
    print(f"get {len(tuple_data)} data success")

def test_redis_set_and_get_multi_thread():
    set_time = timeit.timeit(test_redis_set_multi_thread, number=1)
    get_time = timeit.timeit(test_redis_get_multi_thread, number=1)
    print(f'test_redis_set_multi_thread time: {set_time} seconds')
    print(f'test_redis_get_multi_thread time: {get_time} seconds')


async def test_async_redis_set(semaphore:asyncio.Semaphore):
    r = await async_redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    data = tuple(data.items())
    tasks = [set_async_redis_worker(r, data, semaphore) for data in data]
    completed_tasks = 0
    for task in asyncio.as_completed(tasks):
        result = await task
        completed_tasks += 1
        print(f"set {completed_tasks} success, result: {result}", end="\r")
    print('\n')
    print(f"set {completed_tasks} data success")
async def test_async_redis_get(semaphore:asyncio.Semaphore):
    r = await async_redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    data = tuple(data.items())
    tasks = [get_async_redis_worker(r, data, semaphore) for data in data]
    completed_tasks = 0
    for task in asyncio.as_completed(tasks):
        key,result,expected = await task
        completed_tasks += 1
        if result != expected:
            raise Exception(f"get {key} {expected} failed")
        print(f"get {key} {result} {expected} success", end="\r")
    print('\n')
    print(f"get {completed_tasks} data success")
async def _test_async_redis_set_and_get():
    semaphore = asyncio.Semaphore(50)
    with benchmark_time('test_async_redis_set'):
        await test_async_redis_set(semaphore)
    with benchmark_time('test_async_redis_get'):
        await test_async_redis_get(semaphore)
def test_async_redis_set_and_get():
    with benchmark_time('test_async_redis_set_and_get'):
        asyncio.run(_test_async_redis_set_and_get())



def test_redis_cache_service_set():
    r = RedisCacheService()
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    results = []
    for key, value in data.items():
        results.append(r.set(key, value))
        print(f'set {key} {value} submit success', end='\r')
    print('\n')
    for result in as_completed(results):
        print(f"set {result.result()} success", end="\r")
        # print(f"set {key} {value} success", end="\r")
    print('\n')
    print(f"set {len(data.keys())} data success")

def test_redis_cache_service_get():
    r = RedisCacheService()
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    for key, value in data.items():
        result = r.get(key)
        if result != value:
            raise Exception(f"get {key} {value} failed")
        print(f"get {key} {result} ,expected {value} success", end="\r")
    print('\n')
    print(f"get {len(data.keys())} data success")

def test_redis_cache_service_get_multi_thread():
    r = RedisCacheService()
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    results = []
    for key, _ in data.items():
        results.append(r.get(key,is_multi_thread=True))
    for result in as_completed(results):
        key,result = result.result()
        if result != data[key]:
            raise Exception(f"get {key} {result} ,expected {data[key]} failed")
        print(f"get {key} {result} success", end="\r")
    print('\n')
    print(f"get {len(data.keys())} data success")


def test_redis_cache_service_set_and_get(is_get_multi_thread:bool=False):
    with benchmark_time('test_redis_cache_service_set'):
        test_redis_cache_service_set()
    with benchmark_time('test_redis_cache_service_get'):
        if is_get_multi_thread:
            test_redis_cache_service_get_multi_thread()
        else:
            test_redis_cache_service_get()
if __name__ == '__main__':
    create_random_data()
    # t = timeit.timeit(test_set_random_data, number=1)
    # print(f'test_set_random_data time: {t} seconds')
    # t = timeit.timeit(test_redis_is_append, number=1)
    # print(f'test_redis_is_append time: {t} seconds')
    # t = timeit.timeit(test_muti_redis, number=1)
    # print(f'test_muti_thread_cache time: {t} seconds')
    # t = timeit.timeit(test_async_redis, number=1)
    # print(f'test_async_redis time: {t} seconds')
    # t = timeit.timeit(test_redis_pipeline, number=1)
    # print(f'test_redis_pipeline time: {t} seconds')
    # t = timeit.timeit(test_redis_set_and_get, number=1)
    # print(f'test_redis_set_and_get time: {t} seconds')
    # t = timeit.timeit(test_redis_set_and_get_multi_thread, number=1)
    # print(f'test_redis_set_and_get_multi_thread time: {t} seconds')
    # test_async_redis_set_and_get()
    t = timeit.timeit(lambda: test_redis_cache_service_set_and_get(is_get_multi_thread=True), number=1)
    print(f'test_redis_cache_service_set_and_get time: {t} seconds')