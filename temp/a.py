from src.baidu_sync_for_windows.models.oauth import OauthRecord,OauthInfo
from src.baidu_sync_for_windows.repository import get_default_repository
from src.baidu_sync_for_windows.repository.test import MysqlRepository
from src.baidu_sync_for_windows.dtos import ScanDTO,CompressDTO,VerifyDTO,BackupDTO,HashDTO,EncryptNameCompressDTO,EncryptNameVerifyDTO,EncryptNameBackupDTO

if __name__ == '__main__':
    compress_dto = CompressDTO()
    repository = get_default_repository()
    repository.get(id=1,dto_type=type(compress_dto))
    test_repository = MysqlRepository(engine=repository.engine)
    test_repository.get_by_id(1,type(compress_dto))