from src.constants import PackageTypes
from src.schemas.package_data import AvailableSourcesSchema
from src.utils import *
from src.services.git import *
from src.actions.actions import *

from src.services.directory_structure import verify_file_presence, log_tarballs_structure, log_package_files
from src.services.parsers import parse_mirror
from src.services.file_parsers import update_spec_file, update_hash_file
from src.services.network_requests import RequestsHandler

class TaskHandler:
    def __init__(self, user_data):
        self.user_data: UserDataSchema = user_data
        self.__task_type_to_func = {
            TaskType.UPDATE_PACKAGE: self.__update_package,
            TaskType.CREATE_PACKAGE: None,
            TaskType.PARSE_MIRROR: None,
            TaskType.GET_PACKAGE_FILES: None,
            TaskType.INIT_DIRECTORY_STRUCTURE: None,
            TaskType.EXIT: None
        }

    async def run(self, task_type: TaskType, data: any):
        executor: Callable | None = self.__task_type_to_func.get(task_type)
        if executor is None:
            return 1
        await executor(data)
        return 0

    async def __update_package(self, data: UpdatePackageTaskDataSchema):
        repo_data: RepoDataSchema = prepare_repo(data.repo_url)
        spec_file_path, hash_file_path = verify_file_presence(repo_data.path)

        requests_handler: RequestsHandler = create_requests_handler()

        old_package_data, new_package_data = await get_package_data(requests_handler, spec_file_path)

        available_source_files: AvailableSourcesSchema = await parse_mirror(requests_handler)
        check_for_exit_condition(available_source_files.get_repo_related(repo_data.name), lambda x: len(x) == 0,
                                 f"Sources not found for {repo_data.name}")

        update_spec_file(spec_file_path, old_package_data, new_package_data, data.delete_comments)

        file_hashes: dict[PackageTypes, str] = await requests_handler.download_and_upload_files(
            self.user_data.abf_credentials,
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