import asyncio

from src.actions.TaskHandler import TaskHandler
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
    selected_task: TaskType = TaskType.AWAIT_TASK
    task_handler: TaskHandler = TaskHandler(get_user_data())

    while selected_task != TaskType.EXIT:
        selected_task, task_data = get_task()
        if selected_task == TaskType.EXIT:
            check_for_exit_condition(True, message="Exiting...", type=ExitStatus.EARLY_RETURN)
        if task_data == ExitStatus.NOT_IMPLEMENTED:
            logger.info("This feature is still in development")
            continue
        exit_code: int = await task_handler.run(selected_task, task_data)
        logger.info(f"Task finished with exit code: {exit_code}")

if __name__ == '__main__':
    asyncio.run(main())
