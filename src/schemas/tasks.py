from enum import IntEnum
from typing import Self

from pydantic import BaseModel

from src.utils import handle_bool_input
import src.schemas.tasks_input as cli_input

class TaskData(BaseModel):
    @classmethod
    def from_cli(cls) -> Self:
        return

class UpdatePackageTaskDataSchema(TaskData):
    repo_url: str
    delete_comments: bool

    @classmethod
    def from_cli(cls) -> Self:
        return UpdatePackageTaskDataSchema(
            repo_url=cli_input.get_repo_url(),
            delete_comments=handle_bool_input("Remove present comments y/n? ")
        )

class CloneRemoteRepoTaskDataSchema(TaskData):
    repo_url: str

    @classmethod
    def from_cli(cls) -> Self:
        return CloneRemoteRepoTaskDataSchema(repo_url=cli_input.get_repo_url())


class TaskType(IntEnum):
    UPDATE_PACKAGE = 1
    CREATE_PACKAGE = 2
    PARSE_MIRROR = 3
    GET_PACKAGE_FILES = 4
    CLONE_REMOTE_REPO = 5
    EXIT = 6
    AWAIT_TASK = 7
