import os
import re

from argparse import Namespace
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from rh_pre_commit.tasks import SignOff


class SignOffTaskTest(TestCase):
    @patch("rh_pre_commit.common.hook_installed")
    def test_run(self, mock_hook_installed):
        version_re = re.compile(r"rh-pre-commit\.version:")

        tests = (
            # Success
            (True, 0, "Creating a file for testing"),
            # pre-commit hook not installed
            (False, 1, "Creating a file for testing"),
            # pre-commit hook installed, multiline message
            (True, 0, "Creating a file for testing\n\nMultiple lines\nTesting\n"),
        )
        sign_off = SignOff()

        for i, (hook_installed, expected, message) in enumerate(tests):
            with TemporaryDirectory() as tmp_dir:
                mock_hook_installed.return_value = hook_installed
                tmp_file = os.path.join(tmp_dir, "COMMIT-MSG")

                with open(tmp_file, "w", encoding="UTF-8") as commit_msg:
                    commit_msg.write(message)

                status = sign_off.run(
                    Namespace(
                        command=None,
                        hook_type="commit-msg",
                        commit_msg_filename=tmp_file,
                    )
                )

                self.assertEqual(status, expected, f"test={i}")

                if not hook_installed:
                    continue

                # Confirm the value is present
                with open(tmp_file, encoding="UTF-8") as f:
                    self.assertEqual(len(version_re.findall(f.read())), 1)
                    f.seek(0)
                    self.assertIsNotNone(re.match(message, f.read(), re.MULTILINE))

                # Confirm it doesn't write to the commit message twice if
                # the value is already there (think of ammends)
                # It should strip anything it already finds and replace it
                status = sign_off.run(
                    Namespace(
                        command=None,
                        hook_type="commit-msg",
                        commit_msg_filename=tmp_file,
                    )
                )

                self.assertEqual(status, expected, f"test={i}")
                with open(tmp_file, encoding="UTF-8") as f:
                    self.assertEqual(len(version_re.findall(f.read())), 1)
