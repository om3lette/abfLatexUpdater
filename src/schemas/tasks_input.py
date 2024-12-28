from src.utils import handle_input

def get_repo_url() -> str:
    return handle_input(
        "Type repo url to update: ",
        lambda x: x[-4:] == '.git' and not x.startswith('git')
    )
