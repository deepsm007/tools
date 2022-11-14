import sys
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
                    return line.split(None, 1)[1].strip()

        return None
    except Exception:
        return None


def find_repos(prefix):
    """
    Find all git repos under a given prefix.

    Returns a collection of tuples:
        ("Repo Type", "Path")
    """
    target = f"{os.path.sep}.git"

    for path, _, files in os.walk(prefix):
        if path.endswith(target):
            yield ("R", path)

        elif ".git" in files:
            modpath = read_modfile(path)
            if modpath:
                yield ("M", os.path.join(path, modpath))


def create_parser():
    """
    Create an argparser to handle the arguments for the program
    """
    parser = ArgumentParser(
        prog="rh-multi-pre-commit",
        description="Manage multiple pre-commit hooks for Red Hatters",
    )

    subparsers = parser.add_subparsers(dest="command")

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
    install_parser.add_argument(
        "--path",
        default=".",
        required=False,
        help="The path to install the hooks in"
    )

    subparsers.add_parser(
        "configure",
        help="Configure the pre-commit hooks with the default config",
    )

    subparsers.add_parser(
        "login",
        help="Login to the pattern distribution server",
    )

    return parser


def list_repos(args):
    """
    List all of the repos that would be impacted by the change
    """
    for r_type, r_path, in sorted(find_repos(args.path), key=lambda r: r[1]):
        print(r_type, r_path)

    return 0

def pick_handler(args):
    """
    Figure out how the args should be handled.

    A handler must take the args from the arg parser and return an exit code.
    """

    if args.command == "install":
        if args.check:
            return list_repos

    return lambda args: 0

def main():
    try:
        args = create_parser().parse_args()
        handler = pick_handler(args)

        sys.exit(handler(args))
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(1)
