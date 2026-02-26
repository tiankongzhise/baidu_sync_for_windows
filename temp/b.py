from src.baidu_sync_for_windows.repository.mysql import get_default_repository

if __name__ == '__main__':
    repository = get_default_repository()
    print(repository)