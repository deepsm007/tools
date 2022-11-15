import os

from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from argparse import Namespace

from rh_pre_commit import multi
from rh_pre_commit import config


class MultiPreCommitHookTest(TestCase):
    def test_create_parser(self):
        """
        Simply spot check the arg parser
        """
        parser = multi.create_parser()
        self.assertEqual(parser.prog, "rh-multi-pre-commit")

        # Test install args because we don't want to mess these up
        tests = [
            ("--check --force", True, True),
            ("--force", False, True),
            ("--check", True, False),
            ("--check", True, False),
            ("", False, False),
        ]

        for args, check, force in tests:
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

            self.assertEqual(sorted(expected), sorted(multi.find_repos(tmp_dir)))

    def test_pick_handler(self):
        """
        Test that the right handler is selected when different args are set
        """
        tests = (
            # The default should be to run_pre_commit
            (Namespace(command=None), multi.run_pre_commit),
            # Install --check should list repos
            (Namespace(command="install", check=True), multi.list_repos),
            # Install --check should list repos even if other flags are set
            (Namespace(command="install", check=True, force=True), multi.list_repos),
        )

        for i, (ns, handler) in enumerate(tests):
            self.assertEqual(multi.pick_handler(ns), handler, f"test={i}")

    @patch("pre_commit.main.main")
    def test_run_pre_commit(self, mock_pre_commit_main):
        """
        Confirm the run command passes the right args
        """

        config.RH_MULTI_CONFIG_PATHS = []

        def side_effect(args):
            """
            Simulate different behaviors depending on the path
            """

            # It should fail if fail is in the path for this test
            return 1 if "fail" in " ".join(args) else 0

        mock_pre_commit_main.side_effect = side_effect

        with TemporaryDirectory() as tmp_dir:
            dirs = (
                os.path.join(tmp_dir, "pass"),
                os.path.join(tmp_dir, "skip"),
                os.path.join(tmp_dir, "fail"),
            )

            # Set up the different configs that should be applied

            for d in dirs:
                os.makedirs(d)
                path = os.path.join(d, "config.yaml")
                config.RH_MULTI_CONFIG_PATHS.append(path)

                # Don't create anything in the skip dir this is to test skips
                if "skip" in d:
                    continue

                # Touch the file
                with open(path, "w+", encoding="UTF-8"):
                    pass

            status = multi.run_pre_commit(Namespace())

        self.assertEqual(status, 1)

        # Skip should have been skiped because the config doesn't exist
        self.assertEqual(mock_pre_commit_main.call_count, 2)

        # Should use a run command and they should be ran in order of the configs
        # above
        self.assertEqual(mock_pre_commit_main.mock_calls[0].args[0][0], "run")
        self.assertIn("pass", mock_pre_commit_main.mock_calls[0].args[0][1])
        self.assertEqual(mock_pre_commit_main.mock_calls[1].args[0][0], "run")
        self.assertIn("fail", mock_pre_commit_main.mock_calls[1].args[0][1])
