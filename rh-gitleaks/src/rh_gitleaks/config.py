import os
import platform

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

# Gitleaks Settings
GITLEAKS_VERSION = "7.6.1"
GITLEAKS_SOURCE_ID = f"{GITLEAKS_VERSION}-{PLATFORM_ID}"
GITLEAKS_BIN_PATH = os.path.join(CACHE_DIR, f"gitleaks-{GITLEAKS_SOURCE_ID}")
GITLEAKS_SUPPORTED_VERSIONS = {
    "7.6.1-linux-x86_64": {
        # pylint: disable=line-too-long
        "url": "https://raw.githubusercontent.com/leaktk/bin/main/bin/gitleaks-7.6.1-linux-x86_64",
        "sha256": "ab3d667982b2bfb00e846bd7b751c640216d2bbe0f71e2c53c4514ca415d99ec",
    },
    "7.6.1-darwin-x86_64": {
        # pylint: disable=line-too-long
        "url": "https://raw.githubusercontent.com/leaktk/bin/main/bin/gitleaks-7.6.1-darwin-x86_64",
        "sha256": "5e51a33beb6f358970815ecbbc40c6c28fb785ef6342da9a689713f99fece54f",
    },
    "7.6.1-darwin-arm64": {
        # pylint: disable=line-too-long
        "url": "https://raw.githubusercontent.com/leaktk/bin/main/bin/gitleaks-7.6.1-darwin-arm64",
        "sha256": "eb875959e5994007069490855080bb14657318e5b98cf14da39c2c5480a9f2b3",
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
PATTERNS_REFRESH_INTERVAL = 43200
PATTERNS_PATH = os.path.join(CACHE_DIR, f"gitleaks-{GITLEAKS_VERSION}-patterns.toml")
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
    f"patterns/gitleaks/{GITLEAKS_VERSION}",
)

# Request Settings
REQUEST_USER_AGENT = f"rh-gitleaks/{GITLEAKS_SOURCE_ID}"
