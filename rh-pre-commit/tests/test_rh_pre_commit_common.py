import os

from argparse import Namespace
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from rh_pre_commit import common
from rh_pre_commit import templates

PRE_COMMIT_CONFIG_YAML = """
---
repos:
  - repo: https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git
    rev: main
    hooks:
      - id: rh-pre-commit
      - id: rh-pre-commit.commit-msg
"""


class CommonTest(TestCase):
    hook_types = list(templates.RH_PRE_COMMIT_HOOKS)

    def test_create_parser(self):
        """
        Simply spot check the arg parser
        """
        parser = common.create_parser("foo-bar-baz")
        self.assertEqual(parser.prog, "foo-bar-baz")

        # Test install args because we really don't want to mess these up
        install_tests = (
            ("--check --force", True, True, "."),
            ("--force", False, True, "."),
            ("--check", True, False, "."),
            ("--check --force --path foo", True, True, "foo"),
            ("--force --path=bar", False, True, "bar"),
            ("--check --path baz", True, False, "baz"),
            ("", False, False, "."),
        )
        for hook_type in self.hook_types:
            for args, check, force, path in install_tests:
                ns = parser.parse_args(
                    [f"--hook-type={hook_type}", "install", *args.split()]
                )
                self.assertEqual(
                    ns.check,
                    check,
                    f"check: {ns.check} != {check} for {args}",
                )
                self.assertEqual(
                    ns.force,
                    force,
                    f"force: {ns.force} != {force} for {args}",
                )
                self.assertEqual(
                    ns.path,
                    path,
                    f"path: {ns.path} != {path} for {args}",
                )

        # Test configure args
        configure_tests = (
            ("--configure-git-template", True, False),
            ("--configure-git-template --force", True, True),
            ("", False, False),
        )

        for args, configure_git_template, force in configure_tests:
            ns = parser.parse_args(["configure", *args.split()])
            self.assertEqual(
                ns.configure_git_template,
                configure_git_template,
                f"check: {ns.configure_git_template} != {configure_git_template} for {args}",
            )
            self.assertEqual(
                ns.force,
                force,
                f"check: {ns.force} != {force} for {args}",
            )

    def test_find_repos(self):
        """
        Find repos under a given structure
        """
        with TemporaryDirectory() as tmp_dir:
            expected = [
                ("R", os.path.join(tmp_dir, "foo", "bar", "baz", ".git")),
                ("R", os.path.join(tmp_dir, ".git")),
                ("R", os.path.join(tmp_dir, "test", ".git")),
            ]

            for d in expected:
                os.makedirs(d[1])
                os.makedirs(d[1] + "-not-git")

            # Have a file named .git
            file_test = os.path.join(tmp_dir, "git-file")
            modfile = os.path.join(file_test, ".git")

            os.makedirs(file_test)
            with open(modfile, "w", encoding="UTF-8") as module:
                module.write("gitdir: ../.git/modules/git-file")

            expected.append(("M", os.path.join(file_test, "../.git/modules/git-file")))

            self.assertEqual(sorted(expected), sorted(common.find_repos(tmp_dir)))

    @patch("logging.info")
    @patch("rh_pre_commit.common.find_repos")
    def test_list_repos(self, mock_find_repos, mock_logging_info):
        repos = [
            ("M", "/home/user/repo/.git/modules/foo"),
            ("R", "/home/user/repo/.git"),
        ]

        mock_find_repos.return_value = repos

        common.list_repos(Namespace(path="/home/user"))

        for i, repo in enumerate(sorted(repos, key=lambda r: r[1])):
            call = mock_logging_info.call_args_list[i]

            # Check the type
            self.assertEqual(call.args[1], repo[0])

            # Check the path
            self.assertEqual(call.args[2], repo[1])

    def test_hook_installed(self):
        with TemporaryDirectory() as tmp_dir:
            hook_type = "pre-commit"
            repo_path = os.path.join(tmp_dir, ".git")
            hook_dir = os.path.join(repo_path, "hooks")
            hook_path = os.path.join(hook_dir, hook_type)
            config_path = os.path.join(tmp_dir, ".pre-commit-config.yaml")

            # Just to make sure we're starting off clean
            os.makedirs(hook_dir)
            self.assertFalse(os.path.isfile(hook_path))

            # If it doesn't exist it should fail
            self.assertFalse(common.hook_installed(hook_type, repo_path))

            # It isn't executable nor does it have the right content
            with open(hook_path, "w", encoding="UTF-8") as hook_file:
                hook_file.write("foo")

            self.assertFalse(common.hook_installed(hook_type, repo_path))

            # It has to be the right content
            common.install_hook(
                Namespace(hook_type=hook_type, force=True),
                repo_path,
                "bar",
            )
            self.assertFalse(common.hook_installed(hook_type, repo_path))

            # If it contains rh-pre-commit it's good
            status = common.install_hook(
                Namespace(hook_type=hook_type, force=True),
                repo_path,
                templates.RH_PRE_COMMIT_HOOKS[hook_type],
            )
            self.assertEqual(status, 0)
            self.assertTrue(common.hook_installed(hook_type, repo_path))

            # If it contains rh-multi-pre-commit it's good
            status = common.install_hook(
                Namespace(hook_type=hook_type, force=True),
                repo_path,
                templates.RH_MULTI_PRE_COMMIT_HOOKS[hook_type],
            )
            self.assertEqual(status, 0)
            self.assertTrue(common.hook_installed(hook_type, repo_path))

            # If it just contains pre-commit then it's not valid
            status = common.install_hook(
                Namespace(hook_type=hook_type, force=True),
                repo_path,
                "exec pre-commit",
            )
            self.assertEqual(status, 0)
            self.assertFalse(common.hook_installed(hook_type, repo_path))

            # If pre-commit is configured to run the hook it's valid
            with open(config_path, "w", encoding="UTF-8") as config_file:
                config_file.write(PRE_COMMIT_CONFIG_YAML)

            status = common.install_hook(
                Namespace(hook_type=hook_type, force=True),
                repo_path,
                "exec pre-commit",
            )
            self.assertEqual(status, 0)
            self.assertTrue(common.hook_installed(hook_type, repo_path))
