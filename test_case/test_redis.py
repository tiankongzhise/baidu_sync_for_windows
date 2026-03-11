
import random
import pathlib
import json
from redis import Redis
import timeit
from concurrent.futures import ThreadPoolExecutor,as_completed



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
def test_muti_thread_cache():
    r = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    
    if data is None:
        print("create random data failed")
        return
    data = tuple(data.items())
    tasks = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [executor.submit(set_worker, r, data) for data in data]
        for task in as_completed(tasks):
            print(f"set {task.result()} success", end="\r")
    print(f"set {len(data)} data success")
    end_list = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [executor.submit(get_worker, r, data) for data in data]
        for task in as_completed(tasks):
            data_key,data_get,data_expected = task.result()
            if data_get != data_expected:
                raise Exception(f"get {data_key} {data_expected} failed")
            end_list.append(data_key)
            print(f"get {data_key} {data_get} success", end="\r")
    print('\n')
    print(f"get {len(end_list)} data success")

if __name__ == '__main__':
    create_random_data()
    # t = timeit.timeit(test_set_random_data, number=1)
    # print(f'test_set_random_data time: {t} seconds')
    # t = timeit.timeit(test_redis_is_append, number=1)
    # print(f'test_redis_is_append time: {t} seconds')
    t = timeit.timeit(test_muti_thread_cache, number=1)
    print(f'test_muti_thread_cache time: {t} seconds')