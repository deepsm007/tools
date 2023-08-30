#! /usr/bin/python3

import logging
import os
import sys

from pre_commit import main as pre_commit  # The pre-commit.com library

import rh_pre_commit
from rh_pre_commit import config
from rh_pre_commit import templates
from rh_pre_commit import common


def install(args):
    """
    A handler that sets up pre-commit file
    """
    return common.install(args, templates.RH_MULTI_PRE_COMMIT_HOOK)


def run(_):
    """
    A handler that runs the pre-commit.com package
    """
    status = 0
    if config.local_config_enabled():
        paths = config.RH_MULTI_CONFIG_PATHS
    else:
        paths = (config.RH_MULTI_GLOBAL_CONFIG_PATH,)

    for path in paths:
        if not os.path.isfile(path):
            continue

        status = pre_commit.main(["run", f"--config={path}"])

        if status:
            return status

    return status


def configure(args):
    """
    A handler that resets the config for the tool
    """
    if args.configure_git_template:
        if common.configure_git_template(args, templates.RH_MULTI_PRE_COMMIT_HOOK) != 0:
            return 1

        # So that rh_pre_commit doesn't apply it
        args.configure_git_template = False

    config_path = config.RH_MULTI_GLOBAL_CONFIG_PATH
    try:
        if os.path.lexists(config_path):
            os.remove(config_path)
        if not os.path.lexists(config.CONFIG_DIR):
            os.makedirs(config.CONFIG_DIR)
        with open(config_path, "w", encoding="UTF-8") as config_file:
            config_file.write(templates.RH_MULTI_CONIFG)
    except Exception:
        logging.error("Could not remove or write config %s", config_path)
        return 1

    logging.info("Config updated %s", config_path)

    if config.disable_local_config():
          return 1

    # Apply this to the individual hooks too
    if rh_pre_commit.configure(args) != 0:
        return 1

    return 0


def pick_handler(args):
    """
    Figure out how the args should be handled.

    A handler must take the args from the arg parser and return an exit code.
    """

    if args.command == "update":
        return common.update

    if args.command == "configure":
        return configure

    if args.command == "install":
        if args.check:
            return common.list_repos

        return install

    return run


def main():
    try:
        args = common.create_parser("rh-multi-pre-commit").parse_args()
        handler = pick_handler(args)

        return handler(args)
    except KeyboardInterrupt:
        logging.info("Exiting...")
        return 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )

    sys.exit(main())
