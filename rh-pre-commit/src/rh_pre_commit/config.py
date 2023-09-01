import os

from rh_pre_commit import git


HOME_DIR = os.path.expanduser("~")
DEFAULT_GIT_INIT_TEMPLATE_DIR = os.path.join(HOME_DIR, ".git-template")
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.join(HOME_DIR, ".config")
XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME") or os.path.join(HOME_DIR, ".cache")

CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "pre-commit")
CACHE_DIR = os.path.join(XDG_CACHE_HOME, "pre-commit")

RH_MULTI_GLOBAL_CONFIG_PATH = os.path.join(CONFIG_DIR, "config.yaml")
RH_MULTI_LOCAL_CONFIG_PATH = ".pre-commit-config.yaml"

RH_MULTI_CONFIG_PATHS = (
    RH_MULTI_GLOBAL_CONFIG_PATH,
    RH_MULTI_LOCAL_CONFIG_PATH,
)

DEFAULT_GIT_SECTION = "rh-pre-commit"
DEFAULT_ENABLE_LOCAL_CONFIG_VALUE = "false"
DEFAULT_ENABLE_LOCAL_CONFIG_NAME = "enableLocalConfig"


def disable_local_config():
    return git.config(
        f"{DEFAULT_GIT_SECTION}.{DEFAULT_ENABLE_LOCAL_CONFIG_NAME}",
        DEFAULT_ENABLE_LOCAL_CONFIG_VALUE,
        flags=["global", "bool"],
    ).returncode


def local_config_enabled():
    proc = git.config(
        f"{DEFAULT_GIT_SECTION}.{DEFAULT_ENABLE_LOCAL_CONFIG_NAME}", flags=["bool"]
    )
    config_value = proc.stdout.decode().strip().lower()
    return (config_value or DEFAULT_ENABLE_LOCAL_CONFIG_VALUE) == "true"
