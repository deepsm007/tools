import os

from argparse import ArgumentParser


def read_modfile(path):
    """
    Read the contents of a .git file and return the gitdir value if it exists
    """
    try:
        with open(os.path.join(path, ".git"), encoding="UTF-8") as modfile:
            for line in modfile:
                if line.startswith("gitdir: "):
                    return line.split(None, 1)[1]

        return None
    except Exception:
        return None


def find_repos(prefix):
    """
    Find all git repos under a given prefix.

    Returns a collection of strings
    """
    target = f"{os.path.sep}.git"

    for path, _, files in os.walk(prefix):
        if path.endswith(target):
            yield path

        elif ".git" in files:
            modpath = read_modfile(path)
            if modpath:
                yield os.path.join(path, modpath)


def create_parser():
    """
    Create an argparser to handle the arguments for the program
    """
    parser = ArgumentParser(
        prog="rh-multi-pre-commit",
        description="Manage multiple pre-commit hooks for Red Hatters",
    )

    subparsers = parser.add_subparsers()

    install_parser = subparsers.add_parser(
        "install",
        help="Install the pre-commit hook in a project or projects",
    )
    install_parser.add_argument(
        "--check",
        action="store_true",
        help="Check to see where the hook would be installed, but don't install it",
    )
    install_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Check sub directories for git repos as well",
    )
    install_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing pre-commit hooks"
    )

    subparsers.add_parser(
        "configure", help="Configure the pre-commit hooks with the default config"
    )

    subparsers.add_parser(
        "login",
        help="Login to the pattern distribution server",
    )

    return parser


def main():
    create_parser().parse_args()
