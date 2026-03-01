from baidu_sync_for_windows.service.scan import _scan_file,_scan_directory,scan_service
from pathlib import Path



def test_scan_file():
    target_path :Path = Path(r"D:\测试AI运行\年终聚会（卡芙卡篇） - 副本_2.zip")
    result = _scan_file(target_path)
    print(result)

def test_scan_directory():
    target_path :Path = Path(r"C:/Users/hbc_thinkbook16/Desktop/test2")
    result = _scan_directory(target_path)
    print(result.target_object_size,result.target_object_items_count)

def test_scan_service():
    target_path_list = [
        r"D:\测试AI运行\年终聚会（卡芙卡篇） - 副本_2.zip",
        r"C:/Users/hbc_thinkbook16/Desktop/test2",
    ]
    result = scan_service(target_path_list)
    for item in result:
        print(item.target_object_path,item.target_object_size,item.target_object_items_count)

if __name__ == "__main__":
    # test_scan_file()
    # test_scan_directory()
    test_scan_service()