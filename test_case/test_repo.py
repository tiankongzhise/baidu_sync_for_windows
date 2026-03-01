from baidu_sync_for_windows.repository import get_default_repository
from baidu_sync_for_windows.dtos import HashDTO




def test_is_hashed():
    repository = get_default_repository()
    result = repository.is_processed(HashDTO, 1)
    print(result)

def verytime():
    hash_time = 1772294110384159200
    source_time = 1772294107694819000
    return hash_time > source_time

if __name__ == "__main__":
    test_is_hashed()
    # print(verytime())