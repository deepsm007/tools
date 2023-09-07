import logging
import os

from abc import ABC
from abc import abstractmethod

import rh_gitleaks

from rh_pre_commit import common
from rh_pre_commit import config
from rh_pre_commit import git
from rh_pre_commit import templates


class Task(ABC):
    """
    An abstract base class for implementing a task in the rh-pre-commit
    hook.

    All tasks should inherit from this and should override name, flag and
    optionally default_config_value.
    """

    name = "abstract-task"
    flag = "abstractTask"
    default_config_value = "false"

    _git_section = config.DEFAULT_GIT_SECTION

    def __str__(self):
        return self.name

    def configure(self):
        """
        Set the global config to the default_config_value and return a
        status code.
        """
        return git.config(
            f"{self._git_section}.{self.flag}",
            self.default_config_value,
            flags=["global", "bool"],
        ).returncode

    def enabled(self):
        """
        Make sure this task is turned on in the settings or is enabled by
        default.
        """
        proc = git.config(f"{self._git_section}.{self.flag}", flags=["bool"])
        config_value = proc.stdout.decode().strip().lower()
        return (config_value or self.default_config_value) == "true"

    @abstractmethod
    def run(self, args):
        """
        Run the task and return a status code. A non-zero status code
        is considered a failure.
        """


class CheckSecrets(Task):
    """
    Run rh-gitleaks on unstaged commits
    """

    name = "check-secrets"
    flag = "checkSecrets"
    default_config_value = "true"

    def configure(self, *args, **kwargs):
        """
        Reset the flags but also log in
        """
        return super().configure() or rh_gitleaks.configure(*args, **kwargs)

    def run(self, args):
        """
        Run the check and return a status code. A non-zero status code
        is considered a failure.
        """
        # Make sure this isn't the same as rh_gitleaks.config.BLOCKING_EXIT_CODE
        leak_exit_code = 42

        args = [
            f"--leaks-exit-code={leak_exit_code}",
            "--verbose",
            "--redact",
        ]

        if os.path.isfile(".gitleaks.toml"):
            args.append("--additional-config=.gitleaks.toml")

        rc = rh_gitleaks.main(args)

        if rc == rh_gitleaks.config.BLOCKING_EXIT_CODE:
            return rc

        if rc == leak_exit_code:
            logging.info(templates.LEAK_DETECTED)
            return rc

        # Only return a failing status if leaks are found.
        # There are cases where gitleaks will fail and we don't want to block
        # commits on those
        return 0


class SignOff(Task):
    """
    Add a sign-off message to the commit
    """

    name = "sign-off"
    flag = "signOff"
    default_config_value = "true"

    _git_section = f"{config.DEFAULT_GIT_SECTION}.commit-msg"

    def run(self, args):
        """
        Check that tasks are enabled and then append a SignOff to the commit message
        """

        if not common.hook_installed("pre-commit"):
            logging.error("pre-commit hook not installed")
            return 1

        # Generate sign-off text
        sign_off_msg = [
            f"rh-pre-commit.version: {common.version()}",
        ]

        for task in tasks["pre-commit"]:
            status = "ENABLED" if task.enabled() else "DISABLED"
            sign_off_msg.append(f"rh-pre-commit.{task.name}: {status}")

        # Write the sign-off to file
        with open(args.commit_msg_filename, "a", encoding="UTF-8") as commit_msg_file:
            commit_msg_file.write("\n")
            commit_msg_file.write("\n".join(sign_off_msg))
            commit_msg_file.write("\n")

        return 0


tasks = {"pre-commit": (CheckSecrets(),), "commit-msg": (SignOff(),)}
