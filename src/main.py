import asyncio

import asyncio_atexit

from .schemas import *
from .utils import *
from .services.git import *

from .services.directory_structure import create_work_dir, create_repo_dir, create_repo_subfolders, verify_file_presence, log_tarballs_structure, log_package_files
from .services.parsers import parse_package_data, parse_mirror_for_files
from .services.file_parsers import update_spec_file, update_hash_file, parse_spec_file
from .services.network_requests import RequestsHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)

# TODO account for pearl and macros in spec file
# TODO Non default hash file
# TODO add automatic build request
# TODO Handle file structure change


async def main():
    repo_url: str = handle_input("Type repo url to update: ", lambda x: x[-4:] == '.git' and not x.startswith('git'))
    abf_username: str = handle_input("Type your abf username (email): ", lambda x: '@' in x)
    abf_password: str = handle_input("Type your abf password: ", lambda x: True)
    remove_comments_flag: bool = handle_bool_input("Remove present comments y/n? ")

    create_work_dir()
    repo_name: str = repo_url.split('/')[-1].split('.')[0].replace('texlive-', '')
    repo_path: Path = create_repo_dir(repo_name)

    repo: git.Repo = new_repo(repo_url, repo_path)
    # Git clone requires specified directory to ve empty
    data_path: Path = create_repo_subfolders(repo_path)
    logging.info("Cloned successfully")
    checkout_main(repo)

    spec_file_name, hash_file_name = verify_file_presence(repo_path)
    check_for_exit_condition(hash_file_name, lambda x: x == "", message="Spec file not found")
    check_for_exit_condition(hash_file_name, lambda x: x == "", message="Hash file not found")

    spec_file_path: Path = Path.joinpath(repo_path, spec_file_name)
    hash_file_path: Path = Path.joinpath(repo_path, hash_file_name)

    package_data: SpecFileDataSchema = parse_spec_file(spec_file_path)
    check_for_exit_condition(package_data.is_empty, message="Failed to extract data from spec file")
    logging.info(f"Acquired the following information about the package: Name: {package_data.name} Version: {package_data.version} Release: {package_data.release}")

    logging.info("Getting up to date version from ctan.org")
    requests_handler: RequestsHandler = RequestsHandler()

    async def close_session():
        await requests_handler.close_session()
    asyncio_atexit.register(close_session)

    ctan_package_data: SpecFileDataSchema = await parse_package_data(requests_handler, package_data)

    check_for_exit_condition(is_update_needed(package_data, ctan_package_data), lambda x: not x, f"{package_data.name} is already up to date. Aborting...", type=ExitStatus.EARLY_RETURN)
    logging.info(f"Found version {ctan_package_data.version}")

    logging.info(f"Bumping {package_data.version} to {ctan_package_data.version}")
    available_source_files: AvailableSourcesSchema = await parse_mirror_for_files(requests_handler)
    related_sources: list[FileMetadataSchema] = available_source_files.files[repo_name].general
    check_for_exit_condition(related_sources, lambda x: len(x) == 0, f"Sources not found for {repo_name}")

    update_spec_file(spec_file_path, package_data, ctan_package_data, remove_comments_flag)
    logging.info("Updated spec file")

    file_hashes: dict[PackageTypes, str] = await requests_handler.download_and_upload_files(
        abf_username,
        abf_password,
        package_data.short_name,
        data_path,
        related_sources
    )
    updated_hashes: int = update_hash_file(hash_file_path, file_hashes)
    check_for_exit_condition(updated_hashes, lambda x: x != len(file_hashes), "Not all of the provided hashes were used")

    logging.info("Updated hashes in .abf.yml")

    normalize_line_endings(spec_file_path)
    normalize_line_endings(hash_file_path)
    logging.info("Replaced CRLF and CR with LF")
    log_tarballs_structure(data_path)
    logging.info("List of included files in %files")
    log_package_files(package_data)
    push_to_remote: bool = handle_bool_input(
        "Push to remote origin (check file structure before proceeding) y/n? "
    )
    check_for_exit_condition(push_to_remote, lambda x: not x, "Exiting", type=ExitStatus.EARLY_RETURN)
    logging.info("Adding changes and forming a commit")
    commit_and_push(repo, [spec_file_path, hash_file_path], package_data, ctan_package_data)
    logging.info("Package updated!")
    input('Press "Enter" to continue')

if __name__ == '__main__':
    asyncio.run(main())
