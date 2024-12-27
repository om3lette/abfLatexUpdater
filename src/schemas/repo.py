from pathlib import Path
from git import Repo
from pydantic import BaseModel

from src.constants import WORK_DIR_PATH


class RepoDataSchema(BaseModel):
    url: str
    name: str
    repo: Repo

    @property
    def path(self) -> Path:
        return Path.joinpath(WORK_DIR_PATH, self.name)

    @property
    def data_path(self) -> Path:
        return Path.joinpath(self.path, 'data')

    class Config:
        arbitrary_types_allowed = True