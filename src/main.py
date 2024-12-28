import asyncio
import logging

from src.constants import ExitStatus
from src.schemas.tasks import TaskType

from src.actions.TaskHandler import TaskHandler
from src.actions.actions import get_user_data, get_task

from src.utils import create_logger, check_for_exit_condition

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
