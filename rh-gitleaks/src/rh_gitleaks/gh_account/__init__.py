import sys
import json
import logging
import subprocess  # nosec

import requests

from rh_gitleaks import run_gitleaks


USAGE = """\
NAME
    rh-gitleaks-gh-account - Run rh-gitleaks on all the repos for a GH account

SYNOPSIS
    rh-gitleaks-gh-account gh-namespace [gh-namespace...]

    gh-namespace := { gh-account | gh-organization }

OPTIONS
    gh-account:      A person's username
    gh-organization: The name of a github organization from the URL
"""


class ParsedArgs:
    def __init__(self):
        self.show_help = False
        self.namespaces = []


def parse_args(args):
    """
    Parse the args and return an instance of ParsedArgs
    """
    parsed_args = ParsedArgs()

    if len(args) == 0 or args[0] in ("-h", "--help"):
        parsed_args.show_help = True
    else:
        parsed_args.namespaces.extend(args)

    return parsed_args


def show_help():
    """
    Show help and return an error status
    """
    logging.info(USAGE)
    return 1


def pretty_print_output(proc):
    """
    A callback for cleaning rh_gitleaks output
    """
    try:
        results = list(map(json.loads, proc.stdout.splitlines()))
        output = json.dumps(results, indent=2)
    except Exception:
        output = proc.stdout

    logging.info(output)


def scan_namespaces(namespaces, timeout=60):
    """
    Run rh-gitleaks on per repo per namespace
    """
    for ns in namespaces:
        url = f"https://api.github.com/users/{ns}/repos"

        for repo in requests.get(url, timeout=timeout).json():
            logging.info("Scanning %s", repo["html_url"])
            run_gitleaks(
                ("-q", f"--repo-url={repo['html_url']}"),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                callback=pretty_print_output,
            )

    return 0


def main(args=None):
    """
    Main entrypoint to the program
    """
    args = parse_args(args or sys.argv[1:])
    return show_help() if args.show_help else scan_namespaces(args.namespaces)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    sys.exit(main())
