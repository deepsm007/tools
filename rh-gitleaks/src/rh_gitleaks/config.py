import os
import platform

from importlib import metadata
from urllib import parse

# XDG Folder Info
HOME_DIR = os.path.expanduser("~")
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.join(HOME_DIR, ".config")
XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME") or os.path.join(HOME_DIR, ".cache")

# Platform Information
PLATFORM_SYSTEM = platform.system().lower()
PLATFORM_MACHINE = platform.machine()
PLATFORM_ID = f"{PLATFORM_SYSTEM}-{PLATFORM_MACHINE}"

# Setting Config & Cache Dirs
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "rh-gitleaks")
CACHE_DIR = os.path.join(XDG_CACHE_HOME, "rh-gitleaks")

# Return this exit code to indicate that automation shouldn't continue
BLOCKING_EXIT_CODE = 418

# Rh-Gitleaks Details
try:
    RH_GITLEAKS_VERSION = metadata.version("rh_gitleaks")
except Exception:
    RH_GITLEAKS_VERSION = "unknown"

# Gitleaks Settings
GITLEAKS_BIN_NAMES = ["gitleaks7", "gitleaks"]
GITLEAKS_PATTERN_VERSION= "7.6.1"
LEAKTK_GITLEAKS7_VERSION = "2.0.1"
GITLEAKS_SOURCE_ID = f"leaktk-gitleaks7-{LEAKTK_GITLEAKS7_VERSION}-{PLATFORM_ID}"
GITLEAKS_BIN_PATH = os.path.join(CACHE_DIR, GITLEAKS_SOURCE_ID)
GITLEAKS_SUPPORTED_VERSIONS = {
    "leaktk-gitleaks7-2.0.1-linux-x86_64": {
        # pylint: disable=line-too-long
        "url": "https://raw.githubusercontent.com/leaktk/bin/main/bin/leaktk-gitleaks7-2.0.1-linux-x86_64",
        "sha256": "a579fe7739018c761d04ab2079b6da7768f396744e5ae14c1f2f6a129b5e4cd0",
    },
    "leaktk-gitleaks7-2.0.1-darwin-x86_64": {
        # pylint: disable=line-too-long
        "url": "https://raw.githubusercontent.com/leaktk/bin/main/bin/leaktk-gitleaks7-2.0.1-darwin-x86_64",
        "sha256": "a621e3e7ab1325056ea95d4a99044b71707dd3ac9952415d3400997715e25bfb",
    },
    "leaktk-gitleaks7-2.0.1-darwin-arm64": {
        # pylint: disable=line-too-long
        "url": "https://raw.githubusercontent.com/leaktk/bin/main/bin/leaktk-gitleaks7-2.0.1-darwin-arm64",
        "sha256": "2ce695e7a53360f960f0dba7a0811b65922a1f9cc80bb059638a906405c8077a",
    },
    "leaktk-gitleaks7-2.0.1-linux-aarch64": {
        # pylint: disable=line-too-long
        "url": "https://raw.githubusercontent.com/leaktk/bin/main/bin/leaktk-gitleaks7-2.0.1-linux-arm64",
        "sha256": "dc9d6386387c77c2ba33c789063b138eb80a02754290cbf2de7af5788e47941c",
    },
}

GITLEAKS_BIN_DOWNLOAD_URL = GITLEAKS_SUPPORTED_VERSIONS.get(
    GITLEAKS_SOURCE_ID,
    {},
).get("url")
GITLEAKS_BIN_DOWNLOAD_SHA256SUM = GITLEAKS_SUPPORTED_VERSIONS.get(
    GITLEAKS_SOURCE_ID,
    {},
).get("sha256")

# Pattern Server Settings
PATTERN_SERVER_AUTH_TOKEN_PATH = os.path.join(CONFIG_DIR, "auth.jwt")
# how often to check for new patterns
PATTERNS_REFRESH_INTERVAL = 60 * 60 * 12
# when to refuse to use cached patterns if refresh wasn't possible
PATTERNS_EXPIRED_INTERVAL = PATTERNS_REFRESH_INTERVAL * 14
PATTERNS_PATH = os.path.join(CACHE_DIR, f"gitleaks-{GITLEAKS_PATTERN_VERSION}-patterns.toml")
PATTERN_SERVER_AUTH_TOKEN = os.environ.get("LEAKTK_PATTERN_SERVER_AUTH_TOKEN")
PATTERN_SERVER_URL = os.environ.get(
    "LEAKTK_PATTERN_SERVER_URL",
    "https://patterns.security.redhat.com",
)
PATTERN_SERVER_DOCS_URL = parse.urljoin(
    PATTERN_SERVER_URL,
    "docs",
)
# DEPRECATED: Added for compatibility with older versions of rh-pre-commit
# remove this by/after we reach version 2.0
PATTERNS_SERVER_DOCS_URL = PATTERN_SERVER_DOCS_URL
PATTERN_SERVER_TOKEN_URL = parse.urljoin(
    PATTERN_SERVER_URL,
    "token",
)
PATTERN_SERVER_PATTERNS_URL = parse.urljoin(
    PATTERN_SERVER_URL,
    f"patterns/gitleaks/{GITLEAKS_PATTERN_VERSION}",
)

# Request Settings
REQUEST_USER_AGENT = (
    f"rh-gitleaks/{RH_GITLEAKS_VERSION} ({PLATFORM_SYSTEM} {PLATFORM_MACHINE})"
)

# User interface behaviour settings
LEAKTK_SCANNER_AUTOFETCH = os.environ.get("LEAKTK_SCANNER_AUTOFETCH", "true") in [
    "1",
    "true",
]
