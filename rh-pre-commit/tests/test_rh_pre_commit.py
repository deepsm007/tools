import os

from argparse import Namespace
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

import rh_pre_commit as pre
from rh_pre_commit import common


class PreCommitHookTest(TestCase):
    def test_pick_handler(self):
        """
        Test that the right handler is selected when different args are set
        """
        tests = (
            # The default should be to run
            (
                Namespace(command=None),
                pre.run,
            ),
            # Install --check should list repos
            (
                Namespace(command="install", check=True),
                common.list_repos,
            ),
            # Install --check should list repos even if other flags are set
            (
                Namespace(command="install", check=True, force=True),
                common.list_repos,
            ),
            # Install without check should return the install command
            (
                Namespace(command="install", check=False, force=False),
                pre.install,
            ),
            # Configure should only care about the command
            (
                Namespace(command="configure"),
                pre.configure,
            ),
        )

        for i, (ns, handler) in enumerate(tests):
            self.assertEqual(pre.pick_handler(ns), handler, f"test={i}")

    @patch("rh_pre_commit.checks")
    def test_run(self, mock_rh_pre_commit_checks):
        """
        Confirm the run command passes the right args
        """
        mock_check = Mock()
        mock_rh_pre_commit_checks.__iter__.return_value = [mock_check]

        tests = (
            # Success
            (True, 0, 0),
            # Would fail but disabled
            (False, 1, 0),
            # Enabled and failed
            (True, 1, 1),
        )

        for i, (enabled, run, expected) in enumerate(tests):
            mock_check.reset_mock()
            mock_check.enabled.return_value = enabled
            mock_check.run.return_value = run
            self.assertEqual(pre.run(Namespace()), expected, f"test={i}")

    def test_install(self):
        """
        Test to make sure the install works
        """

        with TemporaryDirectory() as tmp_dir:
            clean_repo = os.path.join(tmp_dir, "repo", ".git")
            existing_hooks = os.path.join(tmp_dir, "existing", ".git")
            just_a_dir = os.path.join(tmp_dir, "some", "dir")

            os.makedirs(clean_repo)
            os.makedirs(existing_hooks)
            os.makedirs(just_a_dir)

            def hook_path(repo_dir, touch=False):
                """
                Helper to stub out the test dirs
                """
                d = os.path.join(repo_dir, "hooks")

                if touch:
                    if not os.path.exists(d):
                        os.makedirs(d)

                    with open(os.path.join(d, "pre-commit"), "w", encoding="UTF-8"):
                        pass

                return os.path.join(d, "pre-commit")

            # Simulate an existing hook
            hook_path(existing_hooks, touch=True)

            #
            # Without --force
            #

            # Run the install now that things are setup
            args = Namespace(check=False, force=False, path=tmp_dir)
            pre.install(args)

            # Was added to the clean repo
            with open(hook_path(clean_repo), encoding="UTF-8") as h:
                self.assertIn("378a113b-5011-4170-9dd7-9ee9e37366b3", h.read())

            # Not to the existing
            with open(hook_path(existing_hooks), encoding="UTF-8") as h:
                self.assertNotIn("378a113b-5011-4170-9dd7-9ee9e37366b3", h.read())

            # Not to the empty dir
            self.assertFalse(os.path.exists(os.path.join(just_a_dir, ".git")))

            #
            # Now with --force
            #

            # Run the install now that things are setup
            args = Namespace(check=False, force=True, path=tmp_dir)
            pre.install(args)

            # Was added to the clean repo
            with open(hook_path(clean_repo), encoding="UTF-8") as h:
                self.assertIn("378a113b-5011-4170-9dd7-9ee9e37366b3", h.read())

            # Now added to the existing due to --force
            with open(hook_path(existing_hooks), encoding="UTF-8") as h:
                self.assertIn("378a113b-5011-4170-9dd7-9ee9e37366b3", h.read())

            # Not to the empty dir
            self.assertFalse(os.path.exists(os.path.join(just_a_dir, ".git")))

    @patch("rh_pre_commit.git.init_template_dir")
    @patch("rh_pre_commit.checks")
    def test_configure(self, mock_rh_pre_commit_checks, mock_git_init_template_dir):
        mock_check = Mock()
        mock_rh_pre_commit_checks.__iter__.return_value = [mock_check]

        with TemporaryDirectory() as tmp_dir:
            init_template_dir = os.path.join(tmp_dir, ".git-template")
            hook_path = os.path.join(init_template_dir, "hooks", "pre-commit")
            mock_git_init_template_dir.return_value = init_template_dir

            # The template hook path shouldn't exist yet
            self.assertFalse(os.path.exists(hook_path))

            mock_check.reset_mock()
            mock_check.configure.return_value = 0
            status = pre.configure(Namespace(configure_git_template=False))
            self.assertEqual(status, 0)

            # The template hook path shouldn't exist yet
            self.assertFalse(os.path.exists(hook_path))

            mock_check.reset_mock()
            mock_check.configure.return_value = 1
            status = pre.configure(Namespace(configure_git_template=True))
            self.assertEqual(status, 1)

            # The template hook path should exist now that the flag was set to
            # True, even though the rest of the hook config failed
            with open(hook_path, encoding="UTF-8") as h:
                self.assertIn("378a113b-5011-4170-9dd7-9ee9e37366b3", h.read())
