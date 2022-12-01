#! /usr/bin/python3
import logging
import sys

from rh_pre_commit import common
from rh_pre_commit import templates
from rh_pre_commit.checks import checks


def run(_):
    """
    A handler that runs the checks
    """
    for check in checks:
        if check.enabled():
            logging.info("Running Check: %s", check)

            if check.run() != 0:
                return 1
        else:
            logging.info("Skipping Check: %s", check)

    return 0


def configure(args):
    """
    A handler that resets the config for the tool
    """
    if args.configure_git_template:
        if common.configure_git_template(args, templates.RH_PRE_COMMIT_HOOK) != 0:
            return 1

    for check in checks:
        if check.configure() != 0:
            logging.error("Error Resetting Check: %s", check)
            return 1

        logging.info("Configured Check: %s", check)

    return 0


def install(args):
    """
    A handler that sets up pre-commit file in the repos
    """
    return common.install(args, templates.RH_PRE_COMMIT_HOOK)


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
        args = common.create_parser("rh-pre-commit").parse_args()
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
