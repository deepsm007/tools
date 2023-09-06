import os

from argparse import Namespace
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

import rh_pre_commit as pre
from rh_pre_commit import common


class PreCommitHookTest(TestCase):
    hooks = [
        ("pre-commit", "13f5c8db-62a3-4ca8-ad21-2f27d83f8068"),
        ("commit-msg", "7f4bf7f0-e2f5-4c86-af41-949a29fb5ef5"),
    ]
    def test_pick_handler(self):
        """
        Test that the right handler is selected when different args are set.
        Alternating hook_type as it should not matter at this point.
        """
        tests = (
            # The default should be to run
            (
                Namespace(command=None, hook_type="pre-commit"),
                pre.run,
            ),
            # Install --check should list repos with pre-commit hook
            (
                Namespace(command="install", check=True, hook_type="commit-msg"),
                common.list_repos,
            ),
            # Install --check should list repos even if other flags are set
            (
                Namespace(
                    command="install", check=True, force=True, hook_type="pre-commit"
                ),
                common.list_repos,
            ),
            # Install without check should return the install command
            (
                Namespace(
                    command="install", check=False, force=False, hook_type="commit-msg"
                ),
                pre.install,
            ),
            # Configure should only care about the command
            (
                Namespace(command="configure", hook_type="pre-commit"),
                pre.configure,
            ),
        )

        for i, (ns, handler) in enumerate(tests):
            self.assertEqual(pre.pick_handler(ns), handler, f"test={i}")

    @patch("rh_pre_commit.tasks")
    def test_run(self, mock_rh_pre_commit_tasks):
        """
        Confirm the run command passes the right args
        """
        mock_check = Mock()
        mock_rh_pre_commit_tasks["commit-msg"].__iter__.return_value = [mock_check]
        mock_rh_pre_commit_tasks["pre-commit"].__iter__.return_value = [mock_check]

        tests = (
            # Success
            ("pre-commit", True, 0, 0),
            # Would fail but disabled
            ("pre-commit", False, 1, 0),
            # Enabled and failed
            ("pre-commit", True, 1, 1),
            # Success
            ("commit-msg", True, 0, 0),
            # Would fail but disabled
            ("commit-msg", False, 1, 0),
            # Enabled and failed
            ("commit-msg", True, 1, 1),
        )

        for i, (hook_type, enabled, run, expected) in enumerate(tests):
            mock_check.reset_mock()
            mock_check.enabled.return_value = enabled
            mock_check.run.return_value = run
            self.assertEqual(
                pre.run(Namespace(hook_type=hook_type)), expected, f"test={i}"
            )

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

            def hook_path(repo_dir, hook_t, touch=False):
                """
                Helper to stub out the test dirs
                """
                d = os.path.join(repo_dir, "hooks")

                if touch:
                    if not os.path.lexists(d):
                        os.makedirs(d)

                    with open(os.path.join(d, hook_t), "w", encoding="UTF-8"):
                        pass

                return os.path.join(d, hook_t)

            for hook_type, hook_uuid in self.hooks:
                # Simulate an existing hook
                hook_path(existing_hooks, hook_type, touch=True)

                #
                # Without --force
                #

                # Run the install now that things are setup
                args = Namespace(
                    check=False, force=False, path=tmp_dir, hook_type=hook_type
                )
                pre.install(args)

                # Was added to the clean repo
                with open(hook_path(clean_repo, hook_type), encoding="UTF-8") as h:
                    self.assertIn(hook_uuid, h.read())

                # Not to the existing
                with open(hook_path(existing_hooks, hook_type), encoding="UTF-8") as h:
                    self.assertNotIn(hook_uuid, h.read())

                # Not to the empty dir
                self.assertFalse(os.path.lexists(os.path.join(just_a_dir, ".git")))

                #
                # Now with --force
                #

                # Run the install now that things are setup
                args = Namespace(
                    check=False, force=True, path=tmp_dir, hook_type=hook_type
                )
                pre.install(args)

                # Was added to the clean repo
                with open(hook_path(clean_repo, hook_type), encoding="UTF-8") as h:
                    self.assertIn(hook_uuid, h.read())

                # Now added to the existing due to --force
                with open(hook_path(existing_hooks, hook_type), encoding="UTF-8") as h:
                    self.assertIn(hook_uuid, h.read())

                # Not to the empty dir
                self.assertFalse(os.path.lexists(os.path.join(just_a_dir, ".git")))

    @patch("rh_pre_commit.git.init_template_dir")
    @patch("rh_pre_commit.tasks")
    def test_configure(self, mock_rh_pre_commit_tasks, mock_git_init_template_dir):
        mock_check = Mock()
        mock_rh_pre_commit_tasks["pre-commit"].__iter__.return_value = [mock_check]

        with TemporaryDirectory() as tmp_dir:
            init_template_dir = os.path.join(tmp_dir, ".git-template")
            for hook_type, hook_uuid in self.hooks:

                hook_path = os.path.join(init_template_dir, "hooks", hook_type)
                mock_git_init_template_dir.return_value = init_template_dir

                # The template hook path shouldn't exist yet
                self.assertFalse(os.path.lexists(hook_path))

                mock_check.reset_mock()
                mock_check.configure.return_value = 0
                status = pre.configure(
                    Namespace(configure_git_template=False, hook_type=hook_type)
                )
                self.assertEqual(status, 0)

                # The template hook path shouldn't exist yet
                self.assertFalse(os.path.lexists(hook_path))

                mock_check.reset_mock()
                mock_check.configure.return_value = 1
                status = pre.configure(
                    Namespace(configure_git_template=True, hook_type=hook_type)
                )
                self.assertEqual(status, 1)

                # The template hook path should exist now that the flag was set to
                # True, even though the rest of the hook config failed
                with open(hook_path, encoding="UTF-8") as h:
                    self.assertIn(hook_uuid, h.read())
