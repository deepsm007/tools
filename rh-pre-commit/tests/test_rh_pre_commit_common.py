import os

from argparse import Namespace
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from rh_pre_commit import common


class CommonTest(TestCase):
    def test_create_parser(self):
        """
        Simply spot check the arg parser
        """
        parser = common.create_parser("foo-bar-baz")
        self.assertEqual(parser.prog, "foo-bar-baz")

        # Test install args because we really don't want to mess these up
        install_tests = (
            ("--check --force", True, True),
            ("--force", False, True),
            ("--check", True, False),
            ("--check", True, False),
            ("", False, False),
        )

        for args, check, force in install_tests:
            ns = parser.parse_args(["install", *args.split()])
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
