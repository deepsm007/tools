import os

from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from argparse import Namespace

from rh_pre_commit import common
from rh_pre_commit import multi
from rh_pre_commit import config


class MultiPreCommitHookTest(TestCase):
    def test_pick_handler(self):
        """
        Test that the right handler is selected when different args are set
        """
        tests = (
            # The default should be to run_hooks
            (
                Namespace(command=None),
                multi.run_hooks,
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
                multi.install_hooks,
            ),
            # Configure should only care about the command
            (
                Namespace(command="configure"),
                multi.configure_hooks,
            ),
        )

        for i, (ns, handler) in enumerate(tests):
            self.assertEqual(multi.pick_handler(ns), handler, f"test={i}")

    @patch("pre_commit.main.main")
    def test_run_hooks(self, mock_pre_commit_main):
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
                with open(path, "w", encoding="UTF-8"):
                    pass

            status = multi.run_hooks(Namespace())

        self.assertEqual(status, 1)

        # Skip should have been skiped because the config doesn't exist
        self.assertEqual(mock_pre_commit_main.call_count, 2)

        # Should use a run command and they should be ran in order of the configs
        # above
        self.assertEqual(mock_pre_commit_main.mock_calls[0].args[0][0], "run")
        self.assertIn("pass", mock_pre_commit_main.mock_calls[0].args[0][1])
        self.assertEqual(mock_pre_commit_main.mock_calls[1].args[0][0], "run")
        self.assertIn("fail", mock_pre_commit_main.mock_calls[1].args[0][1])

    def test_install_hook(self):
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
            multi.install_hooks(args)

            # Was added to the clean repo
            with open(hook_path(clean_repo), encoding="UTF-8") as h:
                self.assertIn("ed00ee75-4516-44ef-8b25-28ca3d18d91a", h.read())

            # Not to the existing
            with open(hook_path(existing_hooks), encoding="UTF-8") as h:
                self.assertNotIn("ed00ee75-4516-44ef-8b25-28ca3d18d91a", h.read())

            # Not to the empty dir
            self.assertFalse(os.path.exists(os.path.join(just_a_dir, ".git")))

            #
            # Now with --force
            #

            # Run the install now that things are setup
            args = Namespace(check=False, force=True, path=tmp_dir)
            multi.install_hooks(args)

            # Was added to the clean repo
            with open(hook_path(clean_repo), encoding="UTF-8") as h:
                self.assertIn("ed00ee75-4516-44ef-8b25-28ca3d18d91a", h.read())

            # Now added to the existing due to --force
            with open(hook_path(existing_hooks), encoding="UTF-8") as h:
                self.assertIn("ed00ee75-4516-44ef-8b25-28ca3d18d91a", h.read())

            # Not to the empty dir
            self.assertFalse(os.path.exists(os.path.join(just_a_dir, ".git")))

    @patch("subprocess.run")
    def test_configure_hooks(self, mock_subprocess_run):
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "true"

        with TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "config.yaml")
            config.RH_MULTI_GLOBAL_CONFIG_PATH = config_path

            # It writes the config file
            self.assertFalse(os.path.exists(config_path))
            multi.configure_hooks(Namespace())
            self.assertTrue(os.path.exists(config_path))

            # It resets the config file
            with open(config_path, "w", encoding="UTF-8") as conf_file:
                conf_file.write("junk")

            with open(config_path, "r", encoding="UTF-8") as conf_file:
                self.assertIn("junk", conf_file.read())

            multi.configure_hooks(Namespace())

            with open(config_path, "r", encoding="UTF-8") as conf_file:
                self.assertNotIn("junk", conf_file.read())
