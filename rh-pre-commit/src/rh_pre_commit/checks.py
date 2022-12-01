import logging
import os

from abc import ABC
from abc import abstractmethod

import rh_gitleaks

from rh_pre_commit import templates
from rh_pre_commit import git


class Check(ABC):
    """
    An abstract base class for implementing a check in the rh-pre-commit
    hook.

    All checks should inherit from this and should override name, flag and
    optionally default_config_value.
    """

    name = "abstract-check"
    flag = "checkAbstract"
    default_config_value = "false"

    _git_section = "rh-pre-commit"

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
    def run(self):
        """
        Run the check and return a status code. A non-zero status code
        is considered a failure.
        """


class SecretsCheck(Check):
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
        return super().configure() or rh_gitleaks.configure(*args, **kwargs)

    def run(self):
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


checks = (SecretsCheck(),)
