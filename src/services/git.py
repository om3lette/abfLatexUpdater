import git
import logging
from src.utils import check_for_exit_condition, handle_bool_input
from src.schemas import SpecFileDataSchema
from src.constants import ExitStatus
from pathlib import Path

logger = logging.getLogger("Git")


def new_repo(repo_url: str, repo_path: Path) -> git.Repo:
    try:
        logger.info("Cloning project repo")
        return git.Repo.clone_from(repo_url, repo_path)
    except git.CommandError as e:
        check_for_exit_condition(True, message="Error occurred while cloning repo. Check your internet connection and insure that abf.io is responding, then try again")


def checkout_main(repo: git.Repo) -> None:
    selected_branch: str = [ref.name for ref in repo.references if ref.name.startswith('origin/')][-1].split('/')[-1]
    if "rosa2023.1" not in selected_branch:
        continue_flag: bool = handle_bool_input(f'"rosa2023.1" branch not found. Proceed with "{selected_branch}" y/n?')
        check_for_exit_condition(not continue_flag, message="Aborting...", type=ExitStatus.EARLY_RETURN)
    repo.git.checkout(selected_branch)


def commit_and_push(repo: git.Repo, files_to_commit: list[Path], old_package_data: SpecFileDataSchema, new_package_data: SpecFileDataSchema) -> None:
    repo.index.add(files_to_commit)
    repo.index.commit(f'Updated package from version "{old_package_data.version}" to "{new_package_data.version}"')
    logger.info("Added files to commit")
    origin = repo.remote('origin')
    origin.push()
    logger.info("Pushed to the remote origin")
