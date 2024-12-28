from enum import IntEnum
from typing import Self

from pydantic import BaseModel

from src.utils import handle_input, handle_bool_input


class TaskData(BaseModel):
    @classmethod
    def from_cli(cls) -> Self:
        return

class UpdatePackageTaskDataSchema(TaskData):
    delete_comments: bool
    repo_url: str

    @classmethod
    def from_cli(cls) -> Self:
        return UpdatePackageTaskDataSchema(
            repo_url=handle_input("Type repo url to update: ", lambda x: x[-4:] == '.git' and not x.startswith('git')),
            delete_comments=handle_bool_input("Remove present comments y/n? ")
        )

class TaskType(IntEnum):
    UPDATE_PACKAGE = 1
    CREATE_PACKAGE = 2
    PARSE_MIRROR = 3
    GET_PACKAGE_FILES = 4
    INIT_DIRECTORY_STRUCTURE = 5
    EXIT = 6
    AWAIT_TASK = 7
