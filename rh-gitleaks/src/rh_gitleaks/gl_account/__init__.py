import sys
import json
import logging
import subprocess  # nosec

from urllib.parse import quote

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


def get_namespace_repos(namespace, timeout=60, page=1, is_user=None):
    server = "gitlab.com"
    slash = namespace.find("/")

    if slash != -1:
        server = namespace[0:slash]
        namespace = namespace[slash + 1 :]

    namespace = quote(namespace, safe="")
    pagination = f"per_page=20&page={page}&order_by=name&sort=asc"
    users_url = f"https://{server}/api/v4/users/{namespace}/projects?{pagination}"
    groups_url = f"https://{server}/api/v4/groups/{namespace}/projects?{pagination}"

    if is_user is True or is_user is None:
        resp = requests.get(users_url, timeout=timeout)
        if resp.status_code != 404:
            return resp.json(), True

    if is_user is False or is_user is None:
        resp = requests.get(groups_url, timeout=timeout)
        if resp.status_code != 404:
            return resp.json(), False

    logging.error("No user or group '%s' found on '%s'", namespace, server)
    sys.exit(1)


def scan_namespaces(namespaces, timeout=60):
    """
    Run rh-gitleaks on per repo per namespace
    """
    for namespace in namespaces:
        page = 1
        is_user = None
        while True:
            repos, is_user = get_namespace_repos(namespace, timeout, page, is_user)

            for repo in repos:
                logging.info("Scanning %s", repo["http_url_to_repo"])
                run_gitleaks(
                    ("-q", f"--repo-url={repo['http_url_to_repo']}"),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    callback=pretty_print_output,
                )

            if len(repos) == 0:
                break

            page += 1

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
