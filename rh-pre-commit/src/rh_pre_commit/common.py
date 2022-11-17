"""
Common functions between rh-pre-commit and rh-multi-pre-commit
"""
import logging
import os
import stat

from argparse import ArgumentParser


def create_parser(prog):
    """
    Create an argparser to handle the arguments for the program
    """
    parser = ArgumentParser(
        prog=prog,
        description="Manage multiple pre-commit hooks for Red Hatters",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "update", help="Update the manager and hooks (global and current dir)"
    )

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
        "--force", action="store_true", help="Overwrite existing pre-commit hooks"
    )
    install_parser.add_argument(
        "--path", default=".", required=False, help="The path to install the hooks in"
    )

    subparsers.add_parser(
        "configure",
        help=f"Reset the global {prog} config",
    )

    return parser


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
    Find all git repos under a given path.

    Returns a tuple generator: gen<(RepoType, GitDir)> where:
        GitDir := "/path/to/the/.git/folder"
        RepoType := ("M"|"R") where:
            M - Module
            R - Regular repo
    """
    target = f"{os.path.sep}.git"

    for path, _, files in os.walk(prefix):
        if path.endswith(target):
            yield ("R", path)

        elif ".git" in files:
            modpath = read_modfile(path)
            if modpath:
                yield ("M", os.path.join(path, modpath))


def update_package(_):
    """
    A handler for updating the packages
    """
    return 1  # TODO


def list_repos(args):
    """
    A handler that lists all of the repos that would be impacted by the change
    """
    repos = sorted(find_repos(args.path), key=lambda r: r[1])

    for repo_type, repo_path in repos:
        logging.info("%s %s", repo_type, repo_path)

    return 0


def install_hook(args, repo_path, content):
    """
    Set up a pre commit hook with the provided content at the
    repo_path
    """
    hooks_dir = os.path.join(repo_path, "hooks")
    hook_path = os.path.join(hooks_dir, "pre-commit")

    # Make sure the hooks dir exists
    if not os.path.exists(hooks_dir):
        try:
            os.mkdir(hooks_dir)
        except Exception:
            logging.error("Could not create hooks dir: %s", hooks_dir)
            return

    if os.path.exists(hook_path):
        if not args.force:
            logging.error("%s already exists. Use --force to overwrite it.", hook_path)
            return

        try:
            os.unlink(hook_path)
        except Exception:
            logging.error("Could not unlink %s", hook_path)
            return

    try:
        with open(hook_path, "w", encoding="UTF-8") as hook_file:
            hook_file.write(content)
    except Exception:
        logging.error("Could not write %s", hook_path)
        return

    try:
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IXUSR)
    except Exception:
        logging.error("Could not make %s executable", hook_path)
        return

    logging.error("Configured %s", hook_path)
