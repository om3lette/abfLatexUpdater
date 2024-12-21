import tarfile

from git import rmtree
from pathlib import Path

from src.schemas import SpecFileDataSchema
from src.utils import check_for_exit_condition
from src.constants import WORK_DIR_PATH, PackageTypes, TARBALL_SUFFIX, SPEC_FILE_SUFFIXES, HASH_FILE_SUFFIXES

import os
import logging

logger = logging.getLogger('DirStructure')


def create_work_dir():
    if WORK_DIR_PATH.is_dir():
        return
    os.mkdir(WORK_DIR_PATH)


def create_repo_dir(repo_name: str) -> Path:
    repo_path: Path = Path.joinpath(WORK_DIR_PATH, repo_name)
    if repo_path.is_dir():
        rmtree(repo_path)
    os.mkdir(repo_path)

    return repo_path


def create_repo_subfolders(repo_path: Path) -> Path:
    data_path: Path = Path.joinpath(repo_path, 'data')
    os.mkdir(data_path)
    return data_path


def sources_save_path(package_name: str, repo_data_path: Path, source_type: PackageTypes) -> [str, Path]:
    extra: str = ""
    if source_type == PackageTypes.SOURCE:
        extra = "source"
    elif source_type == PackageTypes.DOC:
        extra = "doc"
    file_specification: str = f".{extra}"
    file_name: str = f"{package_name}{file_specification if extra else ''}.{TARBALL_SUFFIX}"
    return file_name, Path.joinpath(repo_data_path, file_name)


def verify_file_presence(repo_path: Path) -> tuple[str, str]:
    spec_file_name: str = ""
    hash_file_name: str = ""

    for file in os.listdir(repo_path):
        if '.' not in file:
            continue
        name, suffix = file.rsplit('.', 1)
        if suffix in SPEC_FILE_SUFFIXES:
            spec_file_name = file
        elif suffix in HASH_FILE_SUFFIXES:
            hash_file_name = file

    check_for_exit_condition(hash_file_name, lambda x: x == "", message="Spec file not found")
    check_for_exit_condition(hash_file_name, lambda x: x == "", message="Hash file not found")

    return spec_file_name, hash_file_name


def log_tarballs_structure(data_path: Path):
    for file_name in os.listdir(data_path):
        tarball = tarfile.open(Path.joinpath(data_path, file_name), "r:xz")
        logger.info(f'======Файловая структура "{file_name}"======')
        for name in tarball.getnames():
            logger.info(name)
        tarball.close()


def log_package_files(package_data: SpecFileDataSchema):
    logger.warning("The following list might be incomplete as this feature is still in development")
    for file in package_data.included_files:
        type_verbose: str = 'MAIN'
        if file.type == PackageTypes.DOC:
            type_verbose: str = 'DOC'
        elif file.type == PackageTypes.SOURCE:
            type_verbose = 'SOURCE'
        logger.info(f'{type_verbose}: {file.path}')
