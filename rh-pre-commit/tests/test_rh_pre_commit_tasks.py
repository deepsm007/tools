import os

from argparse import Namespace
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from rh_pre_commit.tasks import SignOff


class SignOffTaskTest(TestCase):
    @patch("rh_pre_commit.common.hook_installed")
    def test_run(self, mock_hook_installed):
        tests = (
            # Success
            (True, 0),
            # pre-commit hook not installed
            (False, 1),
        )
        sign_off = SignOff()

        for i, (hook_installed, expected) in enumerate(tests):
            with TemporaryDirectory() as tmp_dir:
                mock_hook_installed.return_value = hook_installed
                tmp_file = os.path.join(tmp_dir, "COMMIT-MSG")

                with open(tmp_file, "w", encoding="UTF-8") as commit_msg:
                    commit_msg.write("Creating a file for testing")

                status = sign_off.run(
                    Namespace(
                        command=None,
                        hook_type="commit-msg",
                        commit_msg_filename=tmp_file,
                    )
                )

                self.assertEqual(status, expected, f"test={i}")

                if not status:
                    with open(tmp_file, encoding="UTF-8") as f:
                        self.assertIn("rh-pre-commit.version:", f.read())
