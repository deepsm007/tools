import os
import platform

from urllib import parse

HOME_DIR = os.path.expanduser("~")

XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.join(HOME_DIR, ".config")
XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME") or os.path.join(HOME_DIR, ".cache")

CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "rh-gitleaks")
CACHE_DIR = os.path.join(XDG_CACHE_HOME, "rh-gitleaks")

PLATFORM_SYSTEM = platform.system().lower()
PLATFORM_MACHINE = platform.machine()
PLATFORM_ID = f"{PLATFORM_SYSTEM}-{PLATFORM_MACHINE}"

GITLEAKS_VERSION = "7.6.1"
GITLEAKS_SOURCE_ID = f"{PLATFORM_ID}-{GITLEAKS_VERSION}"
GITLEAKS_BIN_PATH = os.path.join(CACHE_DIR, f"gitleaks-{GITLEAKS_SOURCE_ID}")
GITLEAKS_SUPPORTED_VERSIONS = {
    "linux-x86_64-7.6.1": {
        # pylint: disable=line-too-long
        "url": "https://github.com/zricethezav/gitleaks/releases/download/v7.6.1/gitleaks-linux-amd64",
        "sha256": "ab3d667982b2bfb00e846bd7b751c640216d2bbe0f71e2c53c4514ca415d99ec",
    },
    "darwin-x86_64-7.6.1": {
        # pylint: disable=line-too-long
        "url": "https://github.com/zricethezav/gitleaks/releases/download/v7.6.1/gitleaks-darwin-amd64",
        "sha256": "5e51a33beb6f358970815ecbbc40c6c28fb785ef6342da9a689713f99fece54f",
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

USER_AGENT = f"rh-gitleaks/{GITLEAKS_SOURCE_ID}"

PATTERNS_AUTH_JWT_PATH = os.path.join(CONFIG_DIR, "auth.jwt")
PATTERNS_REFRESH_INTERVAL = 43200
PATTERNS_PATH = os.path.join(CACHE_DIR, f"gitleaks-{GITLEAKS_VERSION}-patterns.toml")
PATTERNS_SERVER_URL = os.environ.get(
    "RH_GITLEAKS_PATTERNS_SERVER",
    "https://patterns.security.redhat.com",
)
PATTERNS_SERVER_DOCS_URL = parse.urljoin(
    PATTERNS_SERVER_URL,
    "docs",
)
PATTERNS_SERVER_TOKEN_URL = parse.urljoin(
    PATTERNS_SERVER_URL,
    "token",
)
PATTERNS_SERVER_PATTERNS_URL = parse.urljoin(
    PATTERNS_SERVER_URL,
    f"patterns/gitleaks/{GITLEAKS_VERSION}",
)
