import logging

import asyncio_atexit
from git import Repo
from pathlib import Path

from src.constants import RESERVED_TASK_TYPES, ExitStatus, WORK_DIR_PATH
from src.schemas.package_data import SpecFileDataSchema
from src.schemas.repo import RepoDataSchema

from src.schemas.user_data import UserDataSchema, LoginDataSchema
from src.schemas.tasks import TaskType, UpdatePackageTaskDataSchema, CloneRemoteRepoTaskDataSchema
from src.services.directory_structure import create_work_dir
from src.services.file_parsers import parse_spec_file
from src.services.git import clone_repo, checkout_latest
from src.services.network_requests import RequestsHandler
from src.services.parsers import parse_package_data
from src.utils import handle_input, check_for_exit_condition, is_update_needed


def get_user_data() -> UserDataSchema:
    return UserDataSchema(
        abf_credentials = LoginDataSchema(
            email = handle_input("Type your abf username (email): ", lambda x: '@' in x),
            password = handle_input("Type your abf password: ", lambda x: True)
        )
    )

def get_task() -> tuple[TaskType, any]:
    tasks_prompt: str = "Select a task:\n"
    user_tasks_number: int = len(TaskType) - RESERVED_TASK_TYPES
    for i in range(1, user_tasks_number + 1):
        tasks_prompt += f"{i}) {TaskType(i).name}\n"
    task_number: int = int(handle_input(tasks_prompt, lambda x: x.isdigit() and 0 < int(x) <= user_tasks_number))
    selected_task: TaskType = TaskType.EXIT
    data: any = ExitStatus.NOT_IMPLEMENTED
    if task_number == 1:
        selected_task = TaskType.UPDATE_PACKAGE
        data = UpdatePackageTaskDataSchema.from_cli()
    elif task_number == 2:
        selected_task = TaskType.CREATE_PACKAGE
    elif task_number == 3:
        selected_task = TaskType.PARSE_MIRROR
        data = None
    elif task_number == 4:
        selected_task = TaskType.GET_PACKAGE_FILES
    elif task_number == 5:
        selected_task = TaskType.CLONE_REMOTE_REPO
        data = CloneRemoteRepoTaskDataSchema.from_cli()
    elif task_number == 6:
        selected_task = TaskType.EXIT
        data = None
    return selected_task, data

def prepare_repo(repo_url: str) -> RepoDataSchema:
    create_work_dir()
    repo_name: str = repo_url.split('/')[-1].split('.')[0].replace('texlive-', '')
    repo: Repo = clone_repo(repo_url, Path.joinpath(WORK_DIR_PATH, repo_name), True)

    checkout_latest(repo)

    return RepoDataSchema(
        url=repo_url,
        name=repo_name,
        repo=repo
    )

async def get_package_data(requests_handler: RequestsHandler, spec_file_path: Path) -> tuple[SpecFileDataSchema, SpecFileDataSchema]:
    old_data: SpecFileDataSchema = parse_spec_file(spec_file_path)
    check_for_exit_condition(old_data.is_empty, message="Failed to extract data from spec file")
    logging.info(f"Local package data: {old_data.__str__()}")
    logging.info("Getting up to date data from ctan.org")
    new_data: SpecFileDataSchema = await parse_package_data(requests_handler, old_data)

    update_flag: bool = is_update_needed(old_data, new_data)
    check_for_exit_condition(update_flag, lambda x: not x,f"{old_data.name} is already up to date. Aborting...", type=ExitStatus.EARLY_RETURN)
    logging.info(f"Remote package data: {new_data.__str__()}")
    logging.info(f"Bumping {old_data.version} to {new_data.version}")
    return old_data, new_data

def create_requests_handler() -> RequestsHandler:
    requests_handler: RequestsHandler = RequestsHandler()
    async def close_session():
        await requests_handler.close_session()
    asyncio_atexit.register(close_session)
    return requests_handler
