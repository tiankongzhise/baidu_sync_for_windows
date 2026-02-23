from pathlib import Path
from dtos import ScanDTO
def scan_object(file_path:str|Path)->list[ScanDTO]:
    file_path = Path(file_path)
    if file_path.is_file():
        return [_scan_file(file_path)]
    elif file_path.is_directory():
        result = []
        items = sorted(file_path.iterdir())
        for item in items:
            if item.is_file():
                result.append(_scan_file(item))
            elif item.is_directory():
                result.append(_scan_directory(item))
        return result
    else:
        raise ValueError(f"Invalid file path: {file_path}")



def _scan_file(file_path:str|Path)->ScanDTO:
    ...


def _scan_directory(directory_path:str|Path)->ScanDTO:
    ...