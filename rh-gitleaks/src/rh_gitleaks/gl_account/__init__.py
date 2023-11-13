import sys
import json
import logging
import subprocess  # nosec

import requests

from rh_gitleaks import run_gitleaks


USAGE = """\
NAME
    rh-gitleaks-gl-account - Run rh-gitleaks on all the repos for a GitLab account

SYNOPSIS
    rh-gitleaks-gl-account gl-namespace [gl-namespace...]

    gl-namespace := [gl-server/]{ gl-account | gl-group }

OPTIONS
    gl-server:       A gitlab server hostname
    gl-account:      A person's username
    gl-organization: The name of a gitlab group from the URL
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


def prety_print_output(proc):
    """
    A callback for cleaning rh_gitleaks output
    """
    try:
        results = list(map(json.loads, proc.stdout.splitlines()))
        output = json.dumps(results, indent=2)
    except Exception:
        output = proc.stdout

    logging.info(output)


def get_ns_repos(ns, timeout=60):
    server = "gitlab.com"
    if "/" in ns:
        bits = ns.split("/")
        server = bits[0]
        ns = bits[1]

    usersurl = f"https://{server}/api/v4/users/{ns}/projects"
    groupsurl = f"https://{server}/api/v4/groups/{ns}/projects"

    resp = requests.get(usersurl, timeout=timeout)
    if resp.status_code == 404:
        resp = requests.get(groupsurl, timeout=timeout)

    if resp.status_code == 404:
        logging.error(f"No user or group '{ns}' found on '{server}'")
        sys.exit(1)

    return resp


def scan_namespaces(namespaces, timeout=60):
    """
    Run rh-gitleaks on per repo per namespace
    """
    for ns in namespaces:
        for repo in get_ns_repos(ns, timeout).json():
            logging.info("Scanning %s", repo["http_url_to_repo"])
            run_gitleaks(
                ("-q", f"--repo-url={repo['http_url_to_repo']}"),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                callback=prety_print_output,
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
