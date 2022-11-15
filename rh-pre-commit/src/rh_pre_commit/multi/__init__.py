#! /usr/bin/python3

import os
import shlex
import stat
import sys

from argparse import ArgumentParser

from pre_commit import main as pre_commit  # The pre-commit.com library
from rh_pre_commit import config
from rh_pre_commit import templates


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


def create_parser():
    """
    Create an argparser to handle the arguments for the program
    """
    parser = ArgumentParser(
        prog="rh-multi-pre-commit",
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
        help="Reset the global rh-multi-pre-commit config",
    )

    return parser


def list_repos(args):
    """
    A handler that lists all of the repos that would be impacted by the change
    """
    repos = sorted(find_repos(args.path), key=lambda r: r[1])

    for r_type, r_path in repos:
        print(r_type, r_path)

    return 0


def install_hooks(args):
    """
    A handler that sets up a symlink for the pre-commit hook
    """

    for _, r_path in find_repos(args.path):
        hooks_dir = os.path.join(r_path, "hooks")
        hook_path = os.path.join(hooks_dir, "pre-commit")

        # Make sure the hooks dir exists
        if not os.path.exists(hooks_dir):
            try:
                os.mkdir(hooks_dir)
            except Exception:
                print(f"Could not create hooks dir: {hooks_dir}")
                continue

        if os.path.exists(hook_path):
            if not args.force:
                print(f"{hook_path} already exists. Use --force to overwrite it.")
                continue

            try:
                os.unlink(hook_path)
            except Exception:
                print(f"Could not unlink {hook_path}")
                continue

        try:
            with open(hook_path, "w", encoding="UTF-8") as hook_file:
                hook_file.write(templates.RH_MULTI_PRE_COMMIT_HOOK)
        except Exception:
            print(f"Could not write {hook_path}")
            continue

        try:
            st = os.stat(hook_path)
            os.chmod(hook_path, st.st_mode | stat.S_IXUSR)
        except Exception:
            print(f"Could not make {hook_path} executable")
            continue

        print(f"Configured {hook_path}")


def run_pre_commit(_):
    """
    A handler that runs the pre-commit.com package
    """
    status = 0

    for path in config.RH_MULTI_CONFIG_PATHS:
        if not os.path.exists(path):
            continue

        status = pre_commit.main(
            (
                "run",
                f"--config={path}",
            )
        )

        if status:
            return status

    return status


def pick_handler(args):
    """
    Figure out how the args should be handled.

    A handler must take the args from the arg parser and return an exit code.
    """

    if args.command == "update":
        pass
    elif args.command == "configure":
        pass
    elif args.command == "install":
        if args.check:
            return list_repos

        return install_hooks

    return run_pre_commit


def main():
    try:
        args = create_parser().parse_args()
        handler = pick_handler(args)

        return handler(args)
    except KeyboardInterrupt:
        print("Exiting...")
        return 1


if __name__ == "__main__":
    sys.exit(main())
