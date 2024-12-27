import asyncio

from src.constants import PackageTypes
from src.schemas.package_data import AvailableSourcesSchema
from .utils import *
from .services.git import *
from src.actions.actions import *

from .services.directory_structure import verify_file_presence, log_tarballs_structure, log_package_files
from .services.parsers import parse_mirror
from .services.file_parsers import update_spec_file, update_hash_file
from .services.network_requests import RequestsHandler

# TODO account for pearl and macros in spec file
# TODO Non default hash file
# TODO add automatic build request
# TODO Handle file structure change

logger = create_logger('Root', logging.INFO)

async def main():
    user_data: UserDataSchema = get_user_data()
    selected_task: TaskType = TaskType.AWAIT_TASK

    while selected_task != TaskType.EXIT:
        selected_task, task_data = get_task()
        if selected_task == TaskType.EXIT:
            check_for_exit_condition(True, message="Exiting...", type=ExitStatus.EARLY_RETURN)
        if task_data == ExitStatus.NOT_IMPLEMENTED:
            logger.info("This feature is still in development")
            continue
        repo_data: RepoDataSchema = prepare_repo(task_data.repo_url)
        spec_file_path, hash_file_path = verify_file_presence(repo_data.path)

        requests_handler: RequestsHandler = create_requests_handler()

        old_package_data, new_package_data = await get_package_data(requests_handler, spec_file_path)

        available_source_files: AvailableSourcesSchema = await parse_mirror(requests_handler)
        check_for_exit_condition(available_source_files.get_repo_related(repo_data.name), lambda x: len(x) == 0,f"Sources not found for {repo_data.name}")

        update_spec_file(spec_file_path, old_package_data, new_package_data, task_data.delete_comments)

        file_hashes: dict[PackageTypes, str] = await requests_handler.download_and_upload_files(
            user_data.abf_credentials,
            new_package_data.short_name,
            repo_data.data_path,
            available_source_files.get_repo_related(repo_data.name)
        )
        update_hash_file(hash_file_path, file_hashes)

        normalize_line_endings([spec_file_path, hash_file_path])
        log_tarballs_structure(repo_data.data_path)
        logger.info("List of included files in %files")
        log_package_files(old_package_data)

        check_for_exit_condition(
            handle_bool_input(
                "Push to remote origin (check file structure before proceeding) y/n? "
            ),
            lambda x: not x,
            "Exiting",
            type=ExitStatus.EARLY_RETURN
        )
        commit_and_push(repo_data.repo, [spec_file_path, hash_file_path], old_package_data, new_package_data)
        logger.info("Package updated!")
        input('Press "Enter" to continue')

if __name__ == '__main__':
    asyncio.run(main())
