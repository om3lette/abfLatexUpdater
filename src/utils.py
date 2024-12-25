import fileinput
import logging
import sys

from typing import Callable
from pathlib import Path
from sys import exit

from .constants import ABF_UPLOAD_URI, ExitStatus, MIRROR_BASE_URL, BOOLEAN_INPUT_ANSWERS, ACCEPT_VALUES
from .schemas import SpecFileDataSchema


def handle_input(text: str, validator: Callable) -> str:
    data: str = input(text)
    while not validator(data):
        data: str = input(text)
    return data


def handle_bool_input(text: str) -> bool:
    input_value: str = handle_input(text, lambda x: x.lower() in BOOLEAN_INPUT_ANSWERS)
    return input_value.lower() in ACCEPT_VALUES





def normalize_line_endings(file_path: Path) -> None:
    with open(file_path, 'rb') as file:
        content = file.read()

    # Replace CRLF (Windows-style) with LF (Unix-style)
    content = content.replace(b'\r\n', b'\n')
    # Replace CR (old Mac-style) with LF (Unix-style)
    content = content.replace(b'\r', b'\n')

    with open(file_path, 'wb') as file:
        file.write(content)


def check_for_exit_condition(
        data: any,
        error_checker: Callable = lambda x: x,
        message: str = 'Critical error occurred. Aborting...',
        type: ExitStatus = ExitStatus.ERROR
) -> None:
    if not error_checker(data):
        return
    if type == ExitStatus.ERROR:
        logging.error(message)
    else:
        logging.info(message)
    exit()


def iter_file(file_path: Path, action: Callable, remove_single_quotes: bool = True, read_only: bool = False) -> None:
    f = fileinput.input(file_path, inplace=True)
    last_line: str = ""
    for line in f:
        if line == '\n':
            last_line = line
            sys.stdout.write(line)
            continue
        words: list[str] = line.split()
        section: str = words[0].replace('"', '').replace(':', '').lower()
        new_content: str | None = action(section, line, words)
        if read_only:
            last_line = line
            sys.stdout.write(line)
            continue
        if remove_single_quotes:
            new_content = new_content.replace("'", '')
        sys.stdout.write(new_content)
        last_line = new_content
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
