import json

import aiohttp
import logging

from bs4 import BeautifulSoup, PageElement

from src.services.network_requests import RequestsHandler
from src.utils import check_for_exit_condition, create_logger
from src.constants import MIRROR_BASE_URL, PackageTypes, FILES_CACHE_PATH, ARCHITECTURES_SPECIFIC_PREFIXES
from src.schemas.package_data import SpecFileDataSchema, AvailableSourcesSchema, PackageMetadataSchema, FileMetadataSchema
from dateutil.parser import parse
from datetime import datetime

logger = create_logger('Parser', logging.INFO)


async def get_soup(request_handler: RequestsHandler, url: str) -> BeautifulSoup:
    response: aiohttp.ClientResponse = await request_handler.session.get(url)
    check_for_exit_condition(not response.ok, message="Failed to retrieve package data. Package not found on ctan.org")
    return BeautifulSoup(await response.text(), 'html.parser')


async def parse_package_data(request_handler: RequestsHandler, package_data: SpecFileDataSchema) -> SpecFileDataSchema:
    soup: BeautifulSoup = await get_soup(request_handler, f"https://ctan.org/pkg/{package_data.short_name}")
    table_of_context = soup.find('table')
    logger.info("Collecting up to date data about a package")
    check_for_exit_condition(table_of_context, lambda x: x is None, "Failed to parse page on ctan.org")
    table_rows = table_of_context.find_all('tr')
    new_pacakge_data: SpecFileDataSchema = SpecFileDataSchema(name=package_data.name)
    for row in table_rows:
        table_data_elements = row.find_all('td')
        if table_data_elements[0].text.lower() == 'version':
            new_pacakge_data.version = table_data_elements[-1].text.strip().split()[0].replace('-', '')
            break
    return new_pacakge_data


async def parse_mirror(requests_handler: RequestsHandler) -> AvailableSourcesSchema:
    logger.info("Acquiring available source files list")
    if FILES_CACHE_PATH.is_file():
        logger.info("Found cached data")
        with open(FILES_CACHE_PATH, 'r') as f:
            return AvailableSourcesSchema.model_validate_json(f.read())
    soup: BeautifulSoup = await get_soup(requests_handler, MIRROR_BASE_URL)
    packages_data: list[PageElement] = list(soup.find('pre').children)[2:]
    packages_data_parsed: AvailableSourcesSchema = AvailableSourcesSchema()
    logger.info("Starting parsing process. May take a while")
    for i in range(0, len(packages_data), 2):
        if i % 10000 == 0:
            logger.info(f"Parsed {i // 2}/{len(packages_data) // 2} source files")
        page_elements_package: PageElement = packages_data[i]
        page_elements_metadata: PageElement = packages_data[i + 1]

        source_name_split: list[str] = page_elements_package.text.split('.')
        # [0] - package_name
        # [1] - source type (source | docs | tar => not present => main)
        # [-1], [-2] - file suffix
        # [-3] - potential version such as r15878
        upload_date_str, package_size_str = page_elements_metadata.text.rsplit(maxsplit=1)
        upload_date: datetime = parse(upload_date_str)
        package_size: float = round(int(package_size_str) / 1024, 2) if not package_size_str[-1].isalpha() else float(package_size_str[:-1])

        package_type_str: str = source_name_split[1].lower()
        package_type: PackageTypes = PackageTypes.MAIN
        if package_type_str == 'doc':
            package_type = PackageTypes.DOC
        elif package_type_str == 'source':
            package_type = PackageTypes.SOURCE

        package_storage: PackageMetadataSchema = packages_data_parsed.files[source_name_split[0]]
        file_data: FileMetadataSchema = FileMetadataSchema(type=package_type, upload_time=upload_date, size=package_size)
        if source_name_split[-3][0] == 'r' or any([tag in page_elements_package.text for tag in ARCHITECTURES_SPECIFIC_PREFIXES]):
            file_data.version = source_name_split[-3]
            package_storage.version_specific.append(file_data)
        else:
            package_storage.general.append(file_data)
    logger.info("Parsing completed")
    with open(FILES_CACHE_PATH, 'w') as f:
        f.write(json.dumps(packages_data_parsed.model_dump(), indent=4, sort_keys=True, default=str))
    logger.info("Saved parsed data for future reuse")
    return packages_data_parsed
