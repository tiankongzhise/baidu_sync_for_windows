from baidu_sync_for_windows.dtos import BackupDTO,BaiduPanRefreshResponse,OauthDTO,OauthInfo
from baidu_sync_for_windows.config import get_config
from baidu_sync_for_windows.logger import get_logger
from httpx import Client,AsyncClient
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type,RetryError
from httpx import ReadError, ConnectError
from baidu_sync_for_windows.exception import UploadServiceException
from baidu_sync_for_windows.models.oauth import OauthRecord
from baidu_sync_for_windows.repository import get_default_repository
import os
import json
import time
import traceback
from datetime import datetime
from typing import cast
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import asyncio
import aiofiles

logger = get_logger(bind={'service_name':'backup'})
config = get_config()

def backup_service(source_object_id:int)->tuple[int,BackupDTO|None]:
    repository = get_default_repository('backup')
    if repository.is_processed(source_object_id):
        logger.info(f"source object id: {source_object_id} is already backed up, skip backup")
        return source_object_id, None
    verify_record = repository.get_latest_service_record_by_source_id(source_object_id)
    if verify_record is None:
        raise UploadServiceException(f"source object id: {source_object_id} verify record not found")
    if verify_record.verify_result == 'failed':
        logger.warning(f"source object id: {source_object_id} verify failed, skip backup")
        return source_object_id, None
    backup_object_path = verify_record.verify_compress_file_path
    backup_service = BackupService()
    result = backup_service.backup_task(Path(backup_object_path))
    if result['upload_status'] == 'success':
        return source_object_id, BackupDTO(source_id=source_object_id, backup_object_path=backup_object_path, remote_file_name=result['remote_file_name'], remote_file_hash=result['remote_file_hash'])
    else:
        logger.warning(f"source object id: {source_object_id} backup failed, skip backup")
        return source_object_id, None

class BaiduPanService(object):
    def __init__(self):
        self.logger = get_logger(bind={'service_name':'baidu_pan'})
        self.timeout = config.upload.upload_timeout

    def _request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
        **kwargs,
    ):
        with Client(trust_env=False) as session:
            response = session.request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
            return response.json()

    async def _async_request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
        **kwargs,
    ):
        async with AsyncClient(trust_env=False) as session:
            response = await session.request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
            return response.json()

    def _get_url(self, host: str, endpoint: str):
        if "http" not in host:
            host = f"https://{host}"
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        return f"{host}{endpoint}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=15),
        retry=retry_if_exception_type((ReadError, ConnectError)),
        retry_error_cls=RetryError,
    )
    def refresh_token(self, client_id: str, client_secret: str, refresh_token: str):
        host = "openapi.baidu.com"
        endpoint = "/oauth/2.0/token"
        method = "GET"
        params = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }
        headers = {"User-Agent": "pan.baidu.com"}
        url = self._get_url(host, endpoint)
        rsp_json = self._request(method, url, params=params, headers=headers)
        return BaiduPanRefreshResponse(
            access_token=rsp_json.get("access_token"),
            refresh_token=rsp_json.get("refresh_token"),
            expires_in=rsp_json.get("expires_in"),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=15),
        retry=retry_if_exception_type((ReadError, ConnectError)),
        retry_error_cls=RetryError,
    )
    def precreate(
        self,
        remote_path: str,
        file_size: int,
        block_list: list[str],
        rtype: int = 1,
        isdir: int = 0,
    ):
        host = "pan.baidu.com"
        endpoint = "/rest/2.0/xpan/file"
        method = "POST"
        access_token = os.environ.get("BAIDU_PAN_ACCESS_TOKEN")
        if access_token is None:
            raise UploadServiceException(
                "BaiduPanService precreate出现异常: access_token为空"
            )
        params = {
            "method": "precreate",
            "access_token": access_token,
        }
        body = {
            "path": remote_path,
            "size": file_size,
            "isdir": isdir,
            "rtype": rtype,
            "block_list": json.dumps(block_list),
            "autoinit": 1,
        }
        url = self._get_url(host, endpoint)
        rsp_json = self._request(method, url, params=params, data=body)
        return rsp_json

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=15),
        retry=retry_if_exception_type((ReadError, ConnectError)),
        retry_error_cls=RetryError,
    )
    async def get_locateupload(self, remote_path: str, upload_id: str):
        host = "d.pcs.baidu.com"
        endpoint = "/rest/2.0/pcs/file"
        method = "GET"
        access_token = os.environ.get("BAIDU_PAN_ACCESS_TOKEN")
        params = {
            "method": "locateupload",
            "appid": 250528,
            "access_token": access_token,
            "path": remote_path,
            "uploadid": upload_id,
            "upload_version": 2,
        }
        url = self._get_url(host, endpoint)
        rsp_json = await self._async_request(method, url, params=params)
        return rsp_json

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=15),
        retry=retry_if_exception_type((ReadError, ConnectError)),
        retry_error_cls=RetryError,
    )
    def _generate_host_list(self, host_list: list, block_index):
        """
        根据 hosts 个数和 block_index 生成 host 索引列表

        参数:
        - host_list: hosts 列表
        - block_index: 块索引

        返回:
        - 一个 host 列表，每个元素对应一个 host
        """
        host_count = len(host_list)
        list_length = host_count

        indices = []
        result = []
        # 使用余数确定起始位置
        start_index = block_index % host_count

        for i in range(list_length):
            # 计算当前索引（循环取余）
            current_index = (start_index + i) % host_count
            indices.append(current_index)
        for index in indices:
            result.append(host_list[index])
        return result

    async def upload_block(
        self,
        remote_path: str,
        upload_id: str,
        block_number: int,
        block_data: bytes,
    ):
        rsp_json = await self.get_locateupload(remote_path, upload_id)
        hosts = rsp_json.get("server") or []
        if not hosts:
            raise UploadServiceException(
                "BaiduPanService upload_block出现异常: get_locateupload返回的hosts为空"
            )
        access_token = os.environ.get("BAIDU_PAN_ACCESS_TOKEN")
        if access_token is None:
            raise UploadServiceException(
                "BaiduPanService upload_block出现异常: access_token为空"
            )
        endpoint = "/rest/2.0/pcs/superfile2"
        method = "POST"
        params = {
            "method": "upload",
            "access_token": access_token,
            "type": "tmpfile",
            "uploadid": upload_id,
            "partseq": block_number,
            "path": remote_path,
        }
        files = {"file": block_data}
        generate_host_list = self._generate_host_list(hosts, block_number)
        for host in generate_host_list:
            url = self._get_url(host, endpoint)
            try:
                self.logger.info(
                    f"BaiduPanService upload_block开始上传:{remote_path} {upload_id} {block_number} 节点: {host},可用节点{hosts}"
                )
                start_time = time.time()
                rsp_json = await self._async_request(
                    method, url, params=params, files=files
                )
                end_time = time.time()
                self.logger.info(
                    f"BaiduPanService upload_block{host}节点项目{remote_path} {upload_id} {block_number}上传耗时: {end_time - start_time}秒,速率为{(len(block_data) / (1024 * 1024) / (end_time - start_time)):.2f}MB/s"
                )
                if "md5" in rsp_json:
                    self.logger.info(
                        f"BaiduPanService upload_block成功:{remote_path} {upload_id} {block_number} 节点: {host} 上传成功: {rsp_json}"
                    )
                    return rsp_json
                else:
                    self.logger.info(
                        f"BaiduPanService upload_block{host}节点出现异常:{remote_path} {upload_id} {block_number}上传异常:rsp_json: {rsp_json},尝试下一个节点"
                    )
                    continue
            except ReadError:
                raise UploadServiceException(
                    f"BaiduPanService 并发过大，导致百度pcs关闭了全部节点，请设置config.upload_settings.baidu_pan.upload_concurrency降低并发数，exception: {ReadError}"
                )
            except Exception:
                self.logger.error(
                    f"BaiduPanService upload_block{host}节点出现异常:{remote_path} {upload_id} {block_number}上传异常exception: {traceback.format_exc()},尝试下一个节点"
                )
                continue
        raise UploadServiceException(
            f"BaiduPanService upload_block出现异常: {remote_path} {upload_id} {block_number}上传异常: 所有节点上传失败"
        )

    def create_remote_file(
        self,
        remote_path: str,
        file_size: int,
        block_list: list[str],
        uploadid: str,
        isdir: int = 0,
        rtype: int = 1,
    ):
        host = "pan.baidu.com"
        endpoint = "/rest/2.0/xpan/file"
        method = "POST"
        access_token = os.environ.get("BAIDU_PAN_ACCESS_TOKEN")
        if access_token is None:
            raise UploadServiceException(
                "BaiduPanService create_remote_file出现异常: access_token为空"
            )
        params = {
            "method": "create",
            "access_token": access_token,
        }
        body = {
            "path": remote_path,
            "size": file_size,
            "isdir": isdir,
            "block_list": json.dumps(block_list),
            "uploadid": uploadid,
            "rtype": rtype,
        }
        url = self._get_url(host, endpoint)
        rsp_json = self._request(method, url, params=params, data=body)
        return rsp_json

    def get_user_info(self)->dict:
        host = "pan.baidu.com"
        endpoint = "/rest/2.0/xpan/nas"
        method = "GET"
        access_token = os.environ.get("BAIDU_PAN_ACCESS_TOKEN")
        if access_token is None:
            raise UploadServiceException(
                "BaiduPanService get_user_info出现异常: access_token为空"
            )
        params = {
            "method": "uinfo",
            "access_token": access_token,
        }
        url = self._get_url(host, endpoint)
        rsp_json = self._request(method, url, params=params)
        return rsp_json

class OauthService(object):
    def __init__(self):
        self.logger = get_logger(bind={'service_name':'oauth'})
        self.config = get_config()
        self.oauth_repository = get_default_repository('oauth')
    
    def get_oauth_record(self, platform: str)->OauthRecord|None:
        return self.oauth_repository.get_record_by_platform(platform)
    
    def get_oauth_local(self)->OauthDTO:
        from time import time_ns
        return OauthDTO(
            platform="baidu_pan",
            auth_info=OauthInfo(
                access_token=self.config.oauth.baidu_pan_access_token,
                refresh_token=self.config.oauth.baidu_pan_refresh_token,
                app_key=self.config.oauth.baidu_pan_app_key,
                app_secret=self.config.oauth.baidu_pan_app_secret,
                expires_at=time_ns()
            )
        )
    def is_oauth_expired(self, oauth_dto: OauthDTO|OauthRecord)->bool:
        today_zero = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if isinstance(oauth_dto, OauthDTO):
            expires_at = datetime.fromtimestamp(oauth_dto.auth_info.expires_at)
        else:
            expires_at = oauth_dto.expires_at_local_time
        return expires_at < today_zero
    
    def set_env(self,record:OauthRecord)->None:
        os.environ["BAIDU_PAN_ACCESS_TOKEN"] = cast(str, record.auth_info['access_token'])
        os.environ["BAIDU_PAN_REFRESH_TOKEN"] = cast(str, record.auth_info['refresh_token'])
        os.environ["BAIDU_PAN_APP_KEY"] = cast(str, record.auth_info['app_key'])
        os.environ["BAIDU_PAN_APP_SECRET"] = cast(str, record.auth_info['app_secret'])
    
    def refresh_oauth(self,data:OauthDTO|OauthRecord)->OauthDTO:
        if isinstance(data, OauthDTO):
            refresh_token = data.auth_info.refresh_token.get_secret_value()
            app_key = data.auth_info.app_key.get_secret_value()
            app_secret = data.auth_info.app_secret.get_secret_value()
        else:
            refresh_token = cast(str, data.auth_info['refresh_token'])
            app_key = cast(str, data.auth_info['app_key'])
            app_secret = cast(str, data.auth_info['app_secret'])
        client = BaiduPanService()
        response = client.refresh_token(app_key, app_secret, refresh_token)
        self.logger.debug(f'refresh_oauth response: {response.model_dump_json()}')
        return OauthDTO(
            platform="baidu_pan",
            auth_info=OauthInfo(
                access_token=response.access_token,
                refresh_token=response.refresh_token,
                app_key=app_key, #type: ignore
                app_secret=app_secret, #type: ignore
                expires_at=response.expires_in,
            )
        )


    def oauth(self, platform: str)->None:
        self.logger.log("SERVICE_INFO",f'oauth start: {platform}')
        oauth_record = self.get_oauth_record(platform)
        if oauth_record is None:
            self.logger.log("SERVICE_INFO",'oauth record not found, get oauth local and refresh oauth')
            oauth_dto = self.get_oauth_local()
            new_oauth_dto = self.refresh_oauth(oauth_dto)
            record = self.oauth_repository.save(new_oauth_dto)
        else:
            if self.is_oauth_expired(oauth_record):
                self.logger.log("SERVICE_INFO",'oauth record expired, refresh oauth')
                new_oauth_dto = self.refresh_oauth(oauth_record)
                record = self.oauth_repository.save(new_oauth_dto)
            else:
                self.logger.log("SERVICE_INFO",'oauth record not expired, use oauth record')
                record = oauth_record
        self.set_env(record)
        self.logger.log("SERVICE_INFO",f'oauth end: {platform}')


_OauthService = {}
def get_oauth_service(platform: str)->OauthService:
    global _OauthService
    if _OauthService is None:
        _OauthService[platform] = OauthService()
    elif platform not in _OauthService:
        _OauthService[platform] = OauthService()
    _OauthService[platform].oauth(platform)
    return _OauthService[platform]

class UploadBlockHashService:
    def __init__(
        self,
        algorithm: str |None = "md5",
        upload_chunk_size: int |None = None,
        hash_chunk_size: int |None= None,
        max_workers: int | None = None,
        logger_instance = None,
    ):
        self._config = get_config()
        self.hash_algorithm = algorithm or self._config.upload.algorithm
        self.hash_chunk_size = hash_chunk_size or self._config.hash.hash_chunk_size
        self.upload_chunk_size = upload_chunk_size or self._config.upload.block_size
        self.max_workers = max_workers or self._config.hash.max_workers
        self.logger = logger_instance or get_logger(bind={"service_name": "upload_block_hash_service"})
    
    def get_block_numbers(self, file_path:Path):
        return (file_path.stat().st_size + self.upload_chunk_size - 1) // self.upload_chunk_size

    def get_block_list(self, file_path: str | Path):
        file_path = Path(file_path)
        block_numbers = self.get_block_numbers(file_path)
        # 按块连续分段，每段由一个 worker 顺序读，利于磁盘顺序 I/O
        chunk_list = [
            (i, i * self.upload_chunk_size, self.upload_chunk_size) for i in range(block_numbers)
        ]
        chunk_size = (block_numbers + self.max_workers - 1) // self.max_workers
        ranges = [
            chunk_list[i : i + chunk_size] for i in range(0, block_numbers, chunk_size)
        ]
        task_args = [(str(file_path), r, self.hash_algorithm, self.hash_chunk_size) for r in ranges]
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            result_lists = list(executor.map(self._process_chunk_range, task_args))
        # 按 chunk_id 拼成最终顺序（ranges 已按块顺序切分，各自内部有序）
        results = []
        for r in result_lists:
            results.extend(r)
        results.sort(key=lambda x: x[0])
        block_hash_list = [h for _, h in results]
        return block_hash_list
    @staticmethod
    def _process_chunk_range(args):
        """
        一个 worker 处理多块：只 open 一次文件，顺序 seek+read+hash。
        入参: (file_path, [(chunk_id, offset, size), ...], hash_algorithm)
        返回: [(chunk_id, hash), ...]
        不通过 IPC 传块数据，只传小元组，大文件更快。
        """
        file_path, chunk_list, hash_algorithm, hash_chunk_size = args
        file_path = Path(file_path)
        results = []
        with open(file_path, "rb") as f:
            for chunk_id, offset, size in chunk_list:
                f.seek(offset)
                hash_obj = hashlib.new(hash_algorithm)
                # data = f.read(size)
                # hash_obj.update(data)
                for _ in range(int(size / hash_chunk_size)):
                    data = f.read(hash_chunk_size)
                    hash_obj.update(data)
                results.append((chunk_id, hash_obj.hexdigest().lower()))
        return results


class BackupService(object):
    def __init__(self):
        self.logger = get_logger(bind={'service_name':'backup'})
        self.config = get_config()
        self.baidu_pan_service = BaiduPanService()
        get_oauth_service("baidu_pan")
    
    def _create_remote_file_name(self,upload_file_path:Path)->str:
        remote_dir = self.config.upload.remote_path
        if not remote_dir.startswith("/"):
            remote_dir = f"/{remote_dir}"
        if not remote_dir.endswith("/"):
            remote_dir = f"{remote_dir}/"
        compress_temp_dir = Path(self.config.compress.compress_temp_dir).absolute().as_posix()
        if compress_temp_dir in upload_file_path.absolute().as_posix():
            target_file_name = upload_file_path.relative_to(self.config.compress.compress_temp_dir)
        else:
            target_file_name = upload_file_path.relative_to(Path(upload_file_path.anchor))
        return f"{remote_dir}{target_file_name.as_posix()}"
    
    def precreate_task(self,upload_file_path:Path)->'BackupService':
        block_hash_list = UploadBlockHashService().get_block_list(upload_file_path)
        self._block_hash_list = block_hash_list
        remote_file_name = self._create_remote_file_name(upload_file_path)
        self._remote_file_name = remote_file_name
        file_size = upload_file_path.stat().st_size
        print(f"precreate block_hash_list: {block_hash_list},_block_hash_list: {self._block_hash_list}")
        response = self.baidu_pan_service.precreate(remote_file_name, file_size, block_hash_list)
        if response.get("errno") != 0:
            raise UploadServiceException(f"BaiduPanService precreate出现异常: {response}")
        self._upload_id = response['uploadid']
        return self

    async def upload_block_task(self,upload_file_path:Path)->'BackupService':
        if not hasattr(self, '_upload_id'):
            self.precreate_task(upload_file_path)
        semaphore = asyncio.Semaphore(self.config.upload.upload_concurrency)
        tasks = []
        for index,_ in enumerate(self._block_hash_list):
            tasks.append(self._upload_block_worker(semaphore,upload_file_path,index))
        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            if result['status'] == 'failed':
                self._upload_status = 'failed'
                return self
        self._upload_status = 'success'
        return self
    

    async def _upload_block_worker(self,semaphore:asyncio.Semaphore,upload_file_path:Path,block_index:int)->dict:
        remote_path = self._remote_file_name
        upload_id = self._upload_id
        async with semaphore:
            async with aiofiles.open(upload_file_path, 'rb') as f:
                await f.seek(block_index * self.config.upload.block_size)
                data = await f.read(self.config.upload.block_size)
                try:
                    rsp = await self.baidu_pan_service.upload_block(remote_path, upload_id, block_index, data)
                    result = {
                        'status': 'success',
                        'block_index': block_index,
                        'block_hash': rsp['md5'],
                    }
                    return result
                except Exception as e:
                    result = {
                        'status': 'failed',
                        'block_index': block_index,
                        'error': str(e),
                    }
                    return result

    def create_remote_file_task(self,upload_file_path:Path)->'BackupService':
        if not hasattr(self, '_upload_status'):
            raise UploadServiceException("BaiduPanService create_remote_file_task出现异常: _upload_status为空,请先调用upload_block_task")
        if self._upload_status == 'failed':
            self.logger.warning("BaiduPanService create_remote_file_task出现异常: _upload_status为failed,请先解决上传失败问题")
            self._upload_status = 'failed'
            return self
        block_hash_list = self._block_hash_list
        remote_file_name = self._remote_file_name
        uploadid = self._upload_id
        response = self.baidu_pan_service.create_remote_file(remote_file_name, upload_file_path.stat().st_size, block_hash_list, uploadid)
        if response.get("errno") != 0:
            raise UploadServiceException(f"BaiduPanService create_remote_file出现异常: {response}")
        self._create_remote_file_status = 'success'
        self._remote_file_md5 = response['md5']
        return self

    def backup_task(self,upload_file_path:Path)->dict:
        self.precreate_task(upload_file_path)
        asyncio.run(self.upload_block_task(upload_file_path))
        self.create_remote_file_task(upload_file_path)
        return {
            'remote_file_name': self._remote_file_name,
            'remote_file_md5': getattr(self, '_remote_file_md5', None),
            'upload_status': getattr(self, '_upload_status', None),
        }
