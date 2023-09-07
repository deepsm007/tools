#! /usr/bin/python3
import logging
import sys

from rh_pre_commit import common
from rh_pre_commit import templates
from rh_pre_commit.tasks import tasks


def run(args):
    """
    A handler that runs the checks
    """
    logging.info("Running tasks for hook-type: %s", args.hook_type)
    for task in tasks[args.hook_type]:
        if task.enabled():
            logging.info("Running task: %s", task)

            if task.run(args) != 0:
                logging.info("Task '%s' did not run successfully", task)
                return 1
        else:
            logging.info("Skipping task: %s", task)

    return 0


def configure(args):
    """
    A handler that resets the config for the tool
    """
    if args.configure_git_template:
        template = templates.RH_PRE_COMMIT_HOOK[args.hook_type]
        if common.configure_git_template(args, template) != 0:
            return 1

    for task in tasks[args.hook_type]:
        if task.configure() != 0:
            logging.error("Error configuring %s", task)
            return 1

        logging.info("Configured %s", task)

    return 0


def install(args):
    """
    A handler that sets up pre-commit file in the repos
    """
    return common.install(args, templates.RH_PRE_COMMIT_HOOK[args.hook_type])


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
        if args.version:
            logging.info(common.application_version())
            return 0

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
