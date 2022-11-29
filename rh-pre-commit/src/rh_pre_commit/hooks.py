import logging
import os

import rh_gitleaks
from rh_pre_commit import templates
from rh_pre_commit import git


class Hook:
    name = "abstract-hook"
    flag = "abstractHook"
    default_config_value = "false"

    def __str__(self):
        return self.name

    def configure(self):
        return git.config(
            f"rh-hooks.{self.flag}",
            self.default_config_value,
            flags=["global", "bool"],
        ).returncode

    def enabled(self):
        """
        Make sure this hook is turned on in the settings
        or is enabled by default
        """
        proc = git.config(f"rh-hooks.{self.flag}", flags=["bool"])
        config_value = proc.stdout.decode().strip().lower()
        return (config_value or self.default_config_value) == "true"


class CheckSecrets(Hook):
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

    @staticmethod
    def run():
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


hooks = (CheckSecrets(),)
