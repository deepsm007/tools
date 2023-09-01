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
    An abstract base class for implementing a check in the rh-pre-commit
    hook.

    All checks should inherit from this and should override name, flag and
    optionally default_config_value.
    """

    name = "abstract-check"
    flag = "checkAbstract"
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
        Make sure this check is turned on in the settings or is enabled by
        default.
        """
        proc = git.config(f"{self._git_section}.{self.flag}", flags=["bool"])
        config_value = proc.stdout.decode().strip().lower()
        return (config_value or self.default_config_value) == "true"

    @abstractmethod
    def run(self, args):
        """
        Run the check and return a status code. A non-zero status code
        is considered a failure.
        """


class SecretsCheck(Task):
    """
    Run rh-gitleaks on unstaged commits
    """

    name = "secrets-check"
    flag = "checkSecrets"
    default_config_value = "true"

    def configure(self, *args, **kwargs):
        """
        Reset the flags but also log in
        """
        if rh_gitleaks.load_auth_token():
            return super().configure()

        return super().configure() or rh_gitleaks.configure(*args, **kwargs)

    def run(self, args):
        """
        Run the check and return a status code. A non-zero status code
        is considered a failure.
        """
        leak_exit_code = 42
        args = [
            f"--leaks-exit-code={leak_exit_code}",
            "--verbose",
            "--unstaged",
            "--redact",
            "--format=json",
            "--path=.",
        ]

        if os.path.isfile(".gitleaks.toml"):
            args.append("--additional-config=.gitleaks.toml")

        if rh_gitleaks.main(args) == leak_exit_code:
            logging.info(templates.LEAK_DETECTED)
            return leak_exit_code

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

    _git_section = "rh-pre-commit.commit-msg"

    def run(self, args):
        """
        Check that tasks are enabled and then append a SignOff to the commit message
        """

        if common.check_hooks():
            return 1

        # Generate sign-off text
        sign_off_msg = [f"\nrh-pre-commit.version: {common.application_version()}\n"]
        for task in tasks["pre-commit"]:
            sign_off_msg.append(
                f"rh-pre-commit.{task.name}: " + "OK\n" if task.enabled() else "Off\n"
            )

        # Write the sign-off to file (immediately before end/comments) - I think I can improve this.
        with open(args.commit_msg_filename, "r", encoding="UTF-8") as f:
            lines = f.readlines()

        insert_idx = 0
        for idx, line in enumerate(lines):
            if not line.lstrip().startswith("#"):
                insert_idx = idx
        lines[insert_idx + 1 : 1] = sign_off_msg
        with open(args.commit_msg_filename, "w", encoding="UTF_8") as f:
            f.writelines(lines)

        return 0


tasks = {"pre-commit": (SecretsCheck(),), "commit-msg": (SignOff(),)}
