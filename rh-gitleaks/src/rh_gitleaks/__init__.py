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


def _ensure_dir(dir_path):
    """
    Create a dir if it doesn't exist

    Returns:
        True if the dir exists and False if it couldn't be created
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

    Returns:
        True if the contents matches the expected value
    """
    with open(file_path, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest() == expected


def _download_file(url, dest, headers=None, **kwargs):
    """
    Download a file

    Throws An Exception:
        if the request fails
        if the response fails to write
    """
    _headers = {"User-Agent": config.REQUEST_USER_AGENT}
    _headers.update(headers or {})

    resp = requests.get(url, headers=_headers, timeout=120, **kwargs)
    resp.raise_for_status()

    with open(dest, "wb") as file:
        file.write(resp.content)


def parse_args(args):
    """
    Parse the args for the program

    Returns:
        {
            gitleaks: [args to pass to gitleaks]
            rh_gitleaks: [args to handle in this tool]
        }
    """
    gitleaks_args = []
    rh_gitleaks_args = []

    if len(args):
        if args[0] in ("configure", "login", "logout"):
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
    Lazy pull the gitleaks bin if it doesn't exist and return the path.

    Returns:
        None if it fails to fetch/setup the bin
        gitleaks path str if it exists or was able to be set up
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
    Helper to determine if an update is needed.

    Returns:
        True if the file doesn't exist or it's too old else False
    """

    return (
        not os.path.isfile(path)
        or time.time() - os.stat(path).st_mtime > config.PATTERNS_REFRESH_INTERVAL
    )


def load_auth_token():
    """
    Load the auth token from disk

    Returns:
        The auth token if it exists
        None if it doesn't
    """
    try:
        with open(config.PATTERNS_AUTH_JWT_PATH, "r", encoding="UTF-8") as f:
            auth_jwt = f.read()

            if jwt_valid(auth_jwt):
                return auth_jwt

            return None
    except Exception:
        logging.error("Could not find auth token. Try: rh-gitleaks login")
        return None


def patterns_path():
    """
    Lazy pull patterns and return the path

    Returns:
        The path to the patterns but downloads them if an update is needed
        None if it couldn't be pulled
    """
    if not _ensure_dir(os.path.dirname(config.PATTERNS_PATH)):
        return None

    if patterns_update_needed(config.PATTERNS_PATH):
        logging.info("Downloading patterns from %s", config.PATTERNS_SERVER_URL)

        auth_token = load_auth_token()
        if not auth_token:
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


def run_gitleaks(args, callback=None, **kwargs):
    """
    Run the gitleaks command without capturing stdout/stderr

    Returns:
        the exit status
    """
    bin_path = gitleaks_bin_path()
    if not bin_path:
        return 1

    p_path = patterns_path()
    if not p_path:
        return 1

    # Join provided and default kwargs
    kwargs_with_defaults = {"timeout": 1200}
    kwargs_with_defaults.update(kwargs)

    proc = subprocess.run(  # nosec
        [bin_path, f"--config-path={p_path}", *args],
        check=False,
        shell=False,
        **kwargs_with_defaults,
    )

    if callback:
        callback(proc)

    return proc.returncode


def jwt_valid(token):
    """
    Basic spot checks. Not meant to validate signatures, just that the
    token was copied correctly. The server will validate signatures.

    Returns:
        True if they pass else False
    """

    try:
        payload = jwt.decode(token, options={"verify_signature": False})

        exp = datetime.fromtimestamp(payload["exp"])
        if exp < datetime.now():
            logging.error("That token is expired")
            return False

        iss = payload["iss"]
        if not iss.startswith("pattern-distribution-server"):
            logging.error("%s is an invalid token issuer", iss)
            return False

        logging.info("Token valid until %s", exp.strftime("%Y-%m-%d"))
        return True
    except Exception as e:
        logging.error("Invalid Auth Token: %s", e)
        return False


def configure(auth_jwt=None):
    """
    Run all of the steps to configure the tool. For now it is only a login
    but it may include more steps in the future. This is also to keep the
    tool consistent with other tools in this toolchain.

    Returns:
        A return code for sys.exit
    """
    return login(auth_jwt=auth_jwt)


def login(auth_jwt=None):
    """
    An interactive login session if auth_jwt isn't provided that validates
    a token and writes it to disk.

    Returns:
        A return code for sys.exit
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

    try:
        with open(config.PATTERNS_AUTH_JWT_PATH, "w", encoding="UTF-8") as f:
            f.write(auth_jwt)
    except Exception:
        logging.error("Could not save token: %s", config.PATTERNS_AUTH_JWT_PATH)
        return 1

    logging.info("Successfully logged in")
    return 0


def logout(show_msg=True):
    """
    Remove the auth.jwt

    Returns:
        A return code for sys.exit
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


def main(args=None):
    """
    The main entrypoint into the program. It acceps args so that other
    programs can call this, but if none are provided it defaults to sys.argv
    sans the program's name.

    Returns:
        A return code for sys.exit
    """
    try:
        parsed_args = parse_args(args or sys.argv[1:])

        if parsed_args["rh_gitleaks"]:
            return globals()[parsed_args["rh_gitleaks"][0]]()

        return run_gitleaks(parsed_args["gitleaks"])
    except KeyboardInterrupt:
        logging.error("Exiting...")
        return 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    sys.exit(main())
