import os

import git
import logging

from git import rmtree

from src.utils import check_for_exit_condition, handle_bool_input, create_logger
from src.schemas.package_data import SpecFileDataSchema
from src.constants import ExitStatus, WORK_DIR_PATH
from pathlib import Path

logger = create_logger("Git", logging.INFO)


def clone_repo(repo_url: str, repo_path: Path, create_data_folder: bool = False) -> git.Repo:
    if repo_path.is_dir():
        rmtree(repo_path)
    try:
        logger.info("Cloning project repo...")
        repo: git.Repo = git.Repo.clone_from(repo_url, repo_path)
        if create_data_folder:
            os.mkdir(Path.joinpath(repo_path, 'data'))
        logger.info("Cloned successfully")
        return repo
    except git.CommandError as e:
        check_for_exit_condition(True, message="Error occurred while cloning repo. Check your internet connection and insure that abf.io is responding, then try again", error=str(e))


def checkout_latest(repo: git.Repo) -> None:
    selected_branch: str = [ref.name for ref in repo.references if ref.name.startswith('origin/')][-1].split('/')[-1]
    if "rosa2023.1" not in selected_branch:
        continue_flag: bool = handle_bool_input(f'"rosa2023.1" branch not found. Proceed with "{selected_branch}" y/n?')
        check_for_exit_condition(not continue_flag, message="Aborting...", type=ExitStatus.EARLY_RETURN)
    repo.git.checkout(selected_branch)


def commit_and_push(repo: git.Repo, files_to_commit: list[Path], old_package_data: SpecFileDataSchema, new_package_data: SpecFileDataSchema) -> None:
    logger.info("Adding changes and forming a commit")
    repo.index.add(files_to_commit)
    repo.index.commit(f'Updated package from version "{old_package_data.version}" to "{new_package_data.version}"')
    logger.info("Added files to commit")
    origin = repo.remote('origin')
    try:
        origin.push()
    except git.CommandError as e:
        check_for_exit_condition(True, message="Failed to push to the remote repo", error=str(e))
    logger.info("Pushed to the remote origin")
