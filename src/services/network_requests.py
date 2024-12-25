from pathlib import Path

from src.constants import ABF_UPLOAD_URI, PackageTypes, MIRROR_BASE_URL
from src.schemas import FileMetadataSchema
from src.services.directory_structure import sources_save_path
from src.utils import check_for_exit_condition
import asyncio
import aiohttp
import aiofiles
import logging

logger = logging.getLogger("Network")


class RequestsHandler:
    def __init__(self):
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def close_session(self):
        await self.session.close()

    async def __file_upload_task(self, username: str, password: str, file, hashed_list: dict[PackageTypes, str], file_type: PackageTypes):
        files = {'file_store[file]': file}
        response = await self.session.post(ABF_UPLOAD_URI, auth=aiohttp.BasicAuth(username, password), data=files)
        return_value = (await response.json())['sha1_hash']
        if len(return_value) == 1:
            received_hash: str = return_value[0].split('-')[0].strip()
            # If file already exists hash the following string is returned: "hash - file already exists"
            check_for_exit_condition(
                received_hash,
                lambda x: len(x) == 1,
                "Failed to parse incoming hash. Start the process again for the issue to be resolved"
            )
            hashed_list[file_type] = received_hash
            return
        hashed_list[file_type] = return_value
        return

    async def __file_download_task(self, package_short_name: str, data_path: Path, source_data: FileMetadataSchema, saved_file_paths: list[tuple[Path, PackageTypes]]) -> None:
        source_name, source_save_path = sources_save_path(package_short_name, data_path, source_data.type)
        response: aiohttp.ClientResponse = await self.session.get(MIRROR_BASE_URL + source_name, allow_redirects=True)
        check_for_exit_condition(not response.ok, message=f"Failed to download file with http code {response.status}")
        file = await aiofiles.open(source_save_path, 'wb')
        await file.write(await response.read())
        await file.close()
        saved_file_paths.append((source_save_path, source_data.type))

    async def download_files(self, package_short_name: str, data_path: Path, sources: list[FileMetadataSchema]) -> list[tuple[Path, PackageTypes]]:
        saved_paths: list[tuple[Path, PackageTypes]] = []
        tasks = [
            asyncio.create_task(self.__file_download_task(package_short_name, data_path, source, saved_paths))
            for source in sources
        ]
        try:
            await asyncio.gather(*tasks)
        except aiohttp.ClientConnectionError:
            check_for_exit_condition(True, message="No internet connection. Aborting...")
        return saved_paths

    async def download_and_upload_files(self, username: str, password: str, package_short_name: str, data_path: Path, sources: list[FileMetadataSchema]) -> dict[PackageTypes, str]:
        logger.info(f"Downloading {len(sources)} source files")
        saved_paths: list[tuple[Path, PackageTypes]] = await self.download_files(package_short_name, data_path, sources)
        logger.info("Finished Downloading")
        logger.info(f"Uploading {len(sources)} source files to filestore")
        file_hashes: dict[PackageTypes, str] = await self.upload_to_filestore(username, password, saved_paths)
        logger.info("Source files uploaded")
        return file_hashes

    async def upload_to_filestore(self, username: str, password: str, files_data: list[tuple[Path, PackageTypes]]) -> dict[PackageTypes, str]:
        opened_files: list = []
        file_hashes: dict[PackageTypes, str] = {}

        def close_files():
            for file in opened_files:
                file.close()
        for file_data in files_data:
            opened_files.append(open(file_data[0], 'rb'))
        try:
            tasks = [
                asyncio.create_task(self.__file_upload_task(username, password, file, file_hashes, files_data[i][1]))
                for i, file in enumerate(opened_files)
            ]
            await asyncio.gather(*tasks)
        except Exception:
            close_files()
            check_for_exit_condition(True, message=f"Failed to upload file to filestore. Check for internet connection, credentials spelling and try again")
        close_files()
        return file_hashes
