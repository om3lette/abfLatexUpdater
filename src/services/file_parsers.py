import logging

from src.schemas.package_data import SpecFileDataSchema, PackageTypes, IncludedFileSchema
from src.utils import iter_file, check_for_exit_condition, create_logger
from pathlib import Path

logger = create_logger("FileParser", logging.INFO)


def parse_spec_file(spec_file_path: Path) -> SpecFileDataSchema:
    logger.info("Parsing spec file for package data")
    package_data: SpecFileDataSchema = SpecFileDataSchema()

    def executor(section: str, current_line: str, words: list[str]):
        if section == "version":
            package_data.version = words[1]
        elif section == "name":
            package_data.name = words[1]
        elif section == "release":
            package_data.release = int(words[1])
        elif "texmfdistdir" in section or section == "%doc":
            # Source must be checked first as source files might be flagged with %doc as well
            data_type: PackageTypes = PackageTypes.MAIN
            if "source" in current_line:
                data_type = PackageTypes.SOURCE
            elif section == "%doc":
                data_type = PackageTypes.DOC
            package_data.included_files.append(IncludedFileSchema(path=words[-1], type=data_type))

    iter_file(spec_file_path, executor, read_only=True)
    return package_data


def update_spec_file(spec_file_path: Path, old_data: SpecFileDataSchema, new_data: SpecFileDataSchema, remove_comments: bool = False):
    logger.info("Updating spec file")

    def executor(section: str, current_line: str, words: list[str]):
        if section == "version":
            return current_line.replace(old_data.version, new_data.version, 1)
        if section == "release":
            return current_line.replace(str(old_data.release), str(new_data.release), 1)
        if remove_comments and section == '#':
            # Remove potentially obsolete comments
            return ''
        return current_line
    iter_file(spec_file_path, executor)
    logger.info("Updated spec file")


def update_hash_file(hash_file_path: Path, file_hashes: dict[PackageTypes, str]) -> int:
    logger.info("Updating hash file")

    sources_part_flag: bool = False
    updates_counter: int = 0

    def executor(section: str, current_line: str, words: list[str]):
        nonlocal sources_part_flag
        nonlocal updates_counter
        # Do not change anything besides lines under "sources:", such as "removed_sources" and alike
        if len(words) == 1 and section == "sources":
            sources_part_flag = True
            return current_line
        elif sources_part_flag and len(words) == 1:
            return current_line
        line_base: str = f"  {section}: "
        updates_counter += 1
        if "doc" in section:
            return line_base + f"{file_hashes[PackageTypes.DOC]}\n"
        if "source" in section:
            return line_base + f"{file_hashes[PackageTypes.SOURCE]}\n"
        return line_base + f"{file_hashes[PackageTypes.MAIN]}\n"
    iter_file(hash_file_path, executor)
    check_for_exit_condition(updates_counter, lambda x: x != len(file_hashes),"Not all of the provided hashes were used")
    logger.info("Updated hashes in .abf.yml")
    return updates_counter
