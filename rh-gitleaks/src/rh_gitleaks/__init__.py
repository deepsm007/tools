#! /usr/bin/python3

import hashlib
import logging
import os
import stat
import subprocess  # nosec
import sys
import time

from datetime import datetime

import jwt
import requests

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


def _download_file(url, dest, headers=None, **kwargs):
    """
    Download a file

    Throws an exception if the response fails to write
    """
    _headers = {"User-Agent": config.USER_AGENT}
    _headers.update(headers or {})

    resp = requests.get(url, headers=_headers, timeout=120, **kwargs)
    resp.raise_for_status()

    with open(dest, "wb") as file:
        file.write(resp.content)


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
        or time.time() - os.stat(path).st_mtime > config.PATTERNS_REFRESH_INTERVAL
    )


def load_auth_token():
    try:
        with open(config.PATTERNS_AUTH_JWT_PATH, "r", encoding="UTF-8") as f:
            return f.read()
    except Exception:
        logging.error("Could not find auth token. Try: rh-gitleaks login")
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
            logging.error("Could Not Download Patterns: %s", e)

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
        timeout=1200,
    )

    return proc.returncode


def jwt_valid(token):
    """
    Basic spot checks. Not meant to validate signatures, just that the
    token was copied correctly. The server will validate signatures.
    """

    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = datetime.utcfromtimestamp(payload["exp"])
        iss = payload["iss"]

        if exp < datetime.now():
            logging.error("That token is expired")
            return False

        if not iss.startswith("pattern-distribution-server"):
            logging.error("%s is an invalid token issuer", iss)
            return False

        return True
    except Exception as e:
        logging.error("Invalid Auth Token: %s", e)
        return False


def login(auth_jwt=None):
    """
    An interactive login session if auth_jwt isn't provided
    """
    if not auth_jwt:
        logging.info(
            "To log in, please visit %s and enter in the token below",
            config.PATTERNS_SERVER_TOKEN_URL,
        )
        auth_jwt = input("Token: ").strip()

    if not jwt_valid(auth_jwt):
        logging.info(
            "It seems there was an issue with the token provided. Please try again"
        )
        return 1

    if not os.path.isdir(os.path.dirname(config.PATTERNS_AUTH_JWT_PATH)):
        if not _ensure_dir(os.path.dirname(config.PATTERNS_AUTH_JWT_PATH)):
            return 1

    if logout(show_msg=False) != 0:
        return 1

    with open(config.PATTERNS_AUTH_JWT_PATH, "w", encoding="UTF-8") as f:
        f.write(auth_jwt)

    logging.info("Successfully logged in")
    return 0


def logout(show_msg=True):
    """
    Remove the auth.jwt
    """
    if os.path.exists(config.PATTERNS_AUTH_JWT_PATH):
        try:
            os.remove(config.PATTERNS_AUTH_JWT_PATH)
        except Exception:
            logging.error("Could not remove %s", config.PATTERNS_AUTH_JWT_PATH)
            return 1

    if show_msg:
        logging.info("Successfully logged out")

    return 0


def main():
    args = parse_args(sys.argv[1:])

    if args["rh_gitleaks"]:
        command = args["rh_gitleaks"][0]

        if command == "login":
            return login()

        if command == "logout":
            return logout()

        logging.error("Unrecognized command: %s", command)
        return 1

    # TODO: clean up and test and make sure it matches the old script
    return run_gitleaks(args["gitleaks"])


if __name__ == "__main__":
    sys.exist(main())
