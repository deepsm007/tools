#! /usr/bin/python3

import hashlib
import logging
import os
import stat
import subprocess  # nosec
import sys
import time

from urllib import request

from rh_gitleaks import config

# Logger settings
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def _ensure_dir(dir_path):
    """
    Make sure dirs exist

    Returns True if the directory exists or was created
    """
    if not os.path.isdir(dir_path):
        try:
            os.makedirs(dir_path)
        except Exception:
            logging.error("Could not create dir: %s", dir_path)
            return False

    return True


def _sha256sum_valid(file_path, expected):
    """
    Verify file sha256sums
    """
    with open(file_path, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest() == expected


def _download_file(url, dest, headers={}, **kwargs):
    """
    Download a file

    Throws an exception if the response fails to write
    """
    dl_req = request.Request(
        url=url,
        headers={"User-Agent": config.USER_AGENT, **headers},
        **kwargs,
    )

    with request.urlopen(dl_req) as response:  # nosec
        with open(dest, "wb") as file:
            file.write(response.read())


def parse_args(args):
    """
    Parse the args for the program

    Returns {
        gitleaks: args to pass to gitleaks
        rh_gitleaks: args to handle in this tool
    }
    """
    gitleaks_args = []
    rh_gitleaks_args = []

    if len(args):
        if "login" == args[0] or "logout" == args[0]:
            rh_gitleaks_args.append(args[0])
        else:
            gitleaks_args = args
    else:
        gitleaks_args.append("--help")

    return {
        "gitleaks": gitleaks_args,
        "rh_gitleaks": rh_gitleaks_args,
    }


def gitleaks_bin_path():
    """
    Returns the path to the gitleaks bin path but downloads it if it doesn't
    already exist.
    """
    bin_path = config.GITLEAKS_BIN_PATH
    bin_dir = os.path.dirname(bin_path)

    if not _ensure_dir(bin_dir):
        return None

    if not os.path.isfile(bin_path):
        logging.info("Downloading gitleaks-%s", config.GITLEAKS_SOURCE_ID)
        download_url = config.GITLEAKS_BIN_DOWNLOAD_URL
        download_sha256sum = config.GITLEAKS_BIN_DOWNLOAD_SHA256SUM

        if not (download_url and download_sha256sum):
            logging.error("Your system (%s) is not supported", config.PLATFORM_ID)
            return None

        try:
            _download_file(download_url, bin_path)
            logging.info("Verifying gitleaks-%s", config.GITLEAKS_SOURCE_ID)

            if not _sha256sum_valid(bin_path, download_sha256sum):
                raise Exception("Invalid sha256sum")

            logging.info("Checksum valid (sha256:%s)", download_sha256sum)
        except Exception as e:
            logging.error("%s: %s not created", e, bin_path)

            if os.path.isfile(bin_path):
                os.unlink(bin_path)

            return None

        try:
            st = os.stat(bin_path)
            os.chmod(bin_path, st.st_mode | stat.S_IXUSR)
        except Exception:
            logging.error("Could not make gitleaks executable %s", bin_path)

            if os.path.isfile(bin_path):
                os.unlink(bin_path)

            return None

    return bin_path


def patterns_update_needed(path):
    """
    See if patterns file at <path> is older than the refresh interval or doesn't
    exist
    """

    return (
        not os.path.isfile(path)
        or time.time() - os.stat(p_path).st_mtime > config.PATTERNS_REFRESH_INTERVAL
    )


def load_auth_token():
    try:
        with open(config.PATTERNS_AUTH_JWT_PATH, "r", encoding="UTF-8") as f:
            return f.read()
    except Exception:
        loggin.error("Could not find auth token. Try: rh-gitleaks login")
        return None


def patterns_path():
    """
    Returns the path to the patterns but downloads it if it doesn't already exist.
    """
    if not _ensure_dir(os.path.dirname(config.PATTERNS_PATH)):
        return None

    if patterns_update_needed(config.PATTERNS_PATH):
        logging.info("Downloading patterns from %s", config.PATTERNS_SERVER_URL)

        if not (auth_token := load_auth_token()):
            return None

        try:
            _download_file(
                config.PATTERNS_SERVER_PATTERNS_URL,
                config.PATTERNS_PATH,
                headers={"Authorization": f"Bearer {auth_token}"},
            )
        except Exception as e:
            logging.error("%s: Could now download patterns")

    if not os.path.isfile(config.PATTERNS_PATH):
        return None

    return config.PATTERNS_PATH


def run_gitleaks(args):
    """
    Run the gitleaks command and return the output
    """
    if not ((bin_path := gitleaks_bin_path()) and (p_path := patterns_path())):
        return 1

    proc = subprocess.run(  # nosec
        [bin_path, f"--config-path={p_path}", *args],
        check=False,
        capture_output=False,
        shell=False,
    )

    return proc.returncode


def login(auth_jwt=None):
    """
    An interactive login session if auth_jwt isn't provided
    """
    return 1 # TODO: impl login

def logout():
    """
    Remove the auth.jwt
    """
    if os.path.exists(config.PATTERNS_AUTH_JWT_PATH):
        try:
            os.remove(config.PATTERNS_AUTH_JWT_PATH)
        except Exception:
            logging.error("Could not remove %s", config.PATTERNS_AUTH_JWT_PATH)
            return 1

    logging.info("Successfully logged out")
    return 0

def main():
    args = parse_args(sys.argv[1:])

    if args["rh_gitleaks"]:
        command = args["rh_gitleaks"][0]

        if command == "login":
            return login()
        elif command == "logout":
            return logout()

        logging.error("Unrecognized command: %s", command)
        return 1

    # TODO: clean up and test and make sure it matches the old script
    return run_gitleaks(args["gitleaks"])

if __name__ == "__main__":
    sys.exist(main())
