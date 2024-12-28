import fileinput
import logging
import os
import sys

from datetime import datetime
from typing import Callable
from pathlib import Path
from sys import exit


from .constants import ExitStatus, BOOLEAN_INPUT_ANSWERS, ACCEPT_VALUES, CRASH_LOG_PATH, CACHE_LIFESPAN
from .schemas.package_data import SpecFileDataSchema


def create_logger(name: str, level, file_path: Path | None = None) -> logging.Logger:
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
    if file_path and not file_path.is_file():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
    output_handler = logging.FileHandler(file_path) if file_path is not None else logging.StreamHandler(sys.stdout)
    output_handler.setLevel(level)
    output_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(output_handler)

    logger.propagate = False
    return logger

error_logger = create_logger('Crash', logging.CRITICAL, CRASH_LOG_PATH)

def handle_input(text: str, validator: Callable) -> str:
    data: str = input(text)
    while not validator(data):
        data: str = input(text)
    return data.strip()


def handle_bool_input(text: str) -> bool:
    input_value: str = handle_input(text, lambda x: x.lower() in BOOLEAN_INPUT_ANSWERS)
    return input_value.lower() in ACCEPT_VALUES


def normalize_line_endings(file_paths: list[Path]) -> None:
    for file_path in file_paths:
        with open(file_path, 'rb') as file:
            content = file.read()

        # Replace CRLF (Windows-style) with LF (Unix-style)
        content = content.replace(b'\r\n', b'\n')
        # Replace CR (old Mac-style) with LF (Unix-style)
        content = content.replace(b'\r', b'\n')

        with open(file_path, 'wb') as file:
            file.write(content)
    logging.info("Replaced CRLF and CR with LF")


def check_for_exit_condition(
        data: any,
        error_checker: Callable = lambda x: x,
        message: str = 'Critical error occurred. Aborting...',
        type: ExitStatus = ExitStatus.ERROR,
        error: str | None = None
) -> None:
    if not error_checker(data):
        return
    if type == ExitStatus.ERROR:
        logging.error(message)
    else:
        logging.info(message)

    if error:
        error_logger.critical(error)
    input("Press any key to continue\n")
    exit()


def iter_file(file_path: Path, action: Callable, remove_single_quotes: bool = True, read_only: bool = False) -> None:
    f = fileinput.input(file_path, inplace=True)
    for line in f:
        if line == '\n':
            sys.stdout.write(line)
            continue
        words: list[str] = line.split()
        section: str = words[0].replace('"', '').replace(':', '').lower()
        new_content: str | None = action(section, line, words)
        if read_only:
            sys.stdout.write(line)
            continue
        if remove_single_quotes:
            new_content = new_content.replace("'", '')
        sys.stdout.write(new_content)
    f.close()


def is_update_needed(old_package: SpecFileDataSchema, proposed_update: SpecFileDataSchema) -> bool:
    if old_package.epoch != proposed_update.epoch:
        return old_package.epoch < proposed_update.epoch
    if old_package.version != proposed_update.version:
        # TODO. packaging Version returns an error
        return True
    if old_package.release != proposed_update.release:
        return old_package.release < proposed_update.release
    return False

def is_cache_valid(cache_path: Path) -> bool:
    if not cache_path.is_file():
        return False
    return (datetime.fromtimestamp(cache_path.stat().st_mtime) + CACHE_LIFESPAN) > datetime.today()