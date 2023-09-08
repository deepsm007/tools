"""
Common functions between rh-pre-commit and rh-multi-pre-commit
"""
import logging
import os
import re
import stat

from argparse import ArgumentParser
from importlib import metadata

import yaml

from pre_commit import main as pre_commit  # The pre-commit.com library
from rh_pre_commit import config
from rh_pre_commit import git

HOOK_VARIANT_RE = re.compile(r"\s*exec\s+((rh-(multi-)?)?pre-commit)\b")
GITDIR_RE = re.compile(r"gitdir: (.+)")


def create_parser(prog):
    """
    Create an argparser to handle the arguments for the program
    """
    parser = ArgumentParser(
        prog=prog,
        description="Manage multiple pre-commit hooks for Red Hatters",
    )
    parser.add_argument(
        "--version", "-v", action="store_true", help="Print version information"
    )
    parser.add_argument(
        "--hook-type", default="pre-commit", help="Set the hook type to run."
    )
    parser.add_argument(
        "--commit-msg-filename",
        required=False,
        help="Provide the commit message filename.",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "update", help="Update pre-commit.com style hooks (global and current dir)"
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

    configure_parser = subparsers.add_parser(
        "configure",
        help=f"Reset the global {prog} config",
    )
    configure_parser.add_argument(
        "--configure-git-template",
        action="store_true",
        help="Set init.templateDir if not set and configure the hook for new repos",
    )
    configure_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing init.templateDir pre-commit hook",
    )

    return parser


def search_gitdir(gitfile_path):
    """
    Read the contents of a .git file and return the gitdir value if it exists
    """
    try:
        with open(gitfile_path, encoding="UTF-8") as gitfile:
            return GITDIR_RE.search(gitfile.read()).group(1)
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
            modpath = search_gitdir(os.path.join(path, ".git"))
            if modpath:
                yield ("M", os.path.join(path, modpath))


def update(_):
    """
    A handler for updating the hooks
    """
    status = 0

    for path in config.RH_MULTI_CONFIG_PATHS:
        if not os.path.isfile(path):
            continue

        logging.info("Updating hooks defined in %s", path)
        status = pre_commit.main(["autoupdate", f"--config={path}"])

        if status:
            logging.info("Error updating hooks defined in %s", path)
            return status

    return status


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
    hook_path = os.path.join(hooks_dir, args.hook_type)

    # Make sure the path leading up to the hooks dir exists
    if not os.path.lexists(hooks_dir):
        try:
            os.makedirs(hooks_dir)
        except Exception:
            logging.error("Could not create hooks dir: %s", hooks_dir)
            return 1

    if os.path.lexists(hook_path):
        if not args.force:
            logging.error("%s already exists. Use --force to overwrite it.", hook_path)
            return 1

        try:
            os.unlink(hook_path)
        except Exception:
            logging.error("Could not unlink %s", hook_path)
            return 1

    try:
        with open(hook_path, "w", encoding="UTF-8") as hook_file:
            hook_file.write(content)
    except Exception:
        logging.error("Could not write %s", hook_path)
        return 1

    try:
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IXUSR)
    except Exception:
        logging.error("Could not make %s executable", hook_path)
        return 1

    logging.info("Configured %s", hook_path)
    return 0


def install(args, content):
    """
    Set up the pre-commit hook for multiple repos and optionally the
    init.templateDir
    """
    status = 0

    for _, repo_path in find_repos(args.path):
        if install_hook(args, repo_path, content) != 0:
            # Set the status but keep installing it in the other repos
            status = 1

    return status


def is_rh_pre_commit_repo(repo_url):
    """
    Confirm if the repo URL is this tool's repo URL
    """
    # It is split the way it is to handle both ssh and https clones and
    # clones without the .git suffix.
    return (
        repo_url
        and "gitlab.corp.redhat.com" in repo_url
        and "infosec-public/developer-workbench/tools" in repo_url
    )


def hook_installed_via_local_config(hook_type, repo_path):
    """
    Check a local .pre-commit-config.yaml for the hook type being installed.

    The hook id must match what's in the .pre-commit-hooks.yaml. Having it
    installed in a way other than a .pre-commit-config.yaml or directly installed
    through rh-(multi-)-pre-commit is not supported for this check.
    """
    local_config_path = os.path.join(repo_path, "..", ".pre-commit-config.yaml")

    if not os.path.isfile(local_config_path):
        return False

    hook_id = "rh-pre-commit"
    if hook_type != "pre-commit":
        hook_id += f".{hook_type}"

    try:
        with open(local_config_path, "r", encoding="UTF-8") as local_config_file:
            local_config = yaml.load(local_config_file, Loader=yaml.SafeLoader)

        return hook_id in {
            hook["id"]
            for repo in local_config["repos"]
            if repo and "hooks" in repo and is_rh_pre_commit_repo(repo.get("repo"))
            for hook in repo["hooks"]
            if hook and "id" in hook
        }
    except Exception as e:
        logging.error(e)
        return False


def file_is_executable(path):
    """
    Confirm a file exists and can be executed
    """
    if not os.path.isfile(path):
        return False

    return bool(os.stat(path).st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def search_hook_variant(hook_path):
    """
    Determines what type of pre-commit hook is installed

    rh-pre-commit, rh-multi-pre-commit and pre-commit all contain:

        exec <hook_variant>

    For pre-commit, further checks are needed to confirm it's valid.
    """
    try:
        with open(hook_path, "r", encoding="UTF-8") as hook_file:
            hook_data = hook_file.read()
    except Exception as e:
        logging.error(e)
        return None

    match = HOOK_VARIANT_RE.search(hook_data)
    return match.group(1) if match else None


def hook_installed(hook_type, repo_path=os.path.join(os.getcwd(), ".git")):
    # Handle submodules
    if os.path.isfile(repo_path):
        try:
            repo_path = os.path.join(
                os.path.dirname(repo_path), search_gitdir(repo_path)
            )
        except Exception as e:
            logging.error(e)
            return False

    hook_path = os.path.join(repo_path, "hooks", hook_type)

    if not file_is_executable(hook_path):
        return False

    hook_variant = search_hook_variant(hook_path)
    if not hook_variant:
        return False

    if hook_variant in ("rh-multi-pre-commit", "rh-pre-commit"):
        return True

    if hook_variant == "pre-commit":
        return hook_installed_via_local_config(hook_type, repo_path)

    return False


def configure_git_template(args, content):
    template_dir = git.init_template_dir()

    # Try setting it if it doesn't exist
    if not template_dir:
        git.init_template_dir(config.DEFAULT_GIT_INIT_TEMPLATE_DIR)
        template_dir = git.init_template_dir()

    if not template_dir:
        logging.error("Could not configure template dir %s", template_dir)
        return 1

    return install_hook(args, template_dir, content)


def version():
    try:
        return metadata.version("rh_pre_commit")
    except Exception:
        return "UNKNOWN"
