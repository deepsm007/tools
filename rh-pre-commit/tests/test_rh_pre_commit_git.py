from unittest import TestCase
from unittest.mock import patch

from rh_pre_commit import git


class GitTest(TestCase):
    @patch("subprocess.run")
    def test_run(self, mock_subprocess_run):
        mock_subprocess_run.return_value.returncode = 42
        self.assertEqual(git.run("ls-remote", "foo").returncode, 42)
        call = mock_subprocess_run.call_args

        # Confirm some defaults
        self.assertFalse(call.kwargs["shell"])
        self.assertFalse(call.kwargs["check"])
        self.assertFalse(call.kwargs["capture_output"])
        self.assertIn("timeout", call.kwargs)

        # Confirm the command format
        self.assertEqual(call.args[0], ["git", "ls-remote", "foo"])

    @patch("subprocess.run")
    def test_init_template_dir(self, mock_subprocess_run):
        path = "/foo"
        base_cmd = ["git", "config", "--global", "init.templateDir"]

        tests = (
            # Test a successful set
            (0, path, True, base_cmd + [path]),
            # Test a failed set
            (1, path, False, base_cmd + [path]),
            # Test a sucessful get
            (0, None, path, base_cmd),
            # Test a failed get
            (1, None, None, base_cmd),
        )

        for i, (returncode, value, result, command) in enumerate(tests):
            mock_subprocess_run.reset_mock()
            mock_subprocess_run.return_value.returncode = returncode
            mock_subprocess_run.return_value.stdout = path.encode("UTF-8")

            # Make sure it returns the expected value
            self.assertEqual(git.init_template_dir(value), result, f"test={i}")

            # Make sure the git command is correct
            call = mock_subprocess_run.call_args
            self.assertEqual(call.args[0], command, f"test={i}")
