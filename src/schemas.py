from pydantic import BaseModel, Field
from datetime import datetime
from collections import defaultdict
from src.constants import PackageTypes
from typing import DefaultDict, Annotated


class IncludedFileSchema(BaseModel):
    type: PackageTypes | None
    path: str


class SpecFileDataSchema(BaseModel):
    name: str = Field(default="")
    epoch: int = Field(default=1)
    version: str = Field(default="")
    release: int = Field(default=1)
    included_files: list[IncludedFileSchema] = Field(default_factory=list)

    @property
    def is_empty(self):
        return self.name == "" or self.version == ""

    @property
    def short_name(self) -> str:
        if '-' in self.name:
            return '-'.join(self.name.split('-', 1)[1:])
        return self.name


class FileMetadataSchema(BaseModel):
    version: str = Field(default='')
    type: PackageTypes
    upload_time: datetime
    size: float


class PackageMetadataSchema(BaseModel):
    version_specific: list[FileMetadataSchema] = Field(default_factory=list)
    general: list[FileMetadataSchema] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class AvailableSourcesSchema(BaseModel):
    update_time: datetime = Field(default=datetime.now())
    files: DefaultDict[str, Annotated[PackageMetadataSchema, Field(default_factory=PackageMetadataSchema)]] = defaultdict(PackageMetadataSchema)

    class Config:
        arbitrary_types_allowed = True
