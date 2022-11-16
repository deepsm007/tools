import os
import hashlib

from unittest import TestCase
from unittest.mock import patch
from tempfile import TemporaryDirectory

import rh_gitleaks


class RHGitleaksTest(TestCase):
    def test_parse_args(self):
        tests = (
            # Login should ignore anything that isn't login
            (
                ["login", "--foo"],
                {
                    "gitleaks": [],
                    "rh_gitleaks": ["login"],
                },
            ),
            # Logout should ignore anything that isn't login
            (
                ["logout", "--foo"],
                {
                    "gitleaks": [],
                    "rh_gitleaks": ["logout"],
                },
            ),
            # Other things should be passed to gitleaks
            (
                ["--help"],
                {
                    "gitleaks": ["--help"],
                    "rh_gitleaks": [],
                },
            ),
            # Other things should be passed to gitleaks
            (
                ["foo", "bar", "baz"],
                {
                    "gitleaks": ["foo", "bar", "baz"],
                    "rh_gitleaks": [],
                },
            ),
            # No args should pass "--help" to gitleaks
            (
                [],
                {
                    "gitleaks": ["--help"],
                    "rh_gitleaks": [],
                },
            ),
        )

        for i, (args, expected) in enumerate(tests):
            actual = rh_gitleaks.parse_args(args)
            self.assertDictEqual(actual, expected, f"test={i}")

    def test_gitleaks_bin_path(self):
        """
        Make sure it pulls and validates a version of gitleaks
        """
        download_sha256sum = rh_gitleaks.config.GITLEAKS_BIN_DOWNLOAD_SHA256SUM

        with TemporaryDirectory() as tmp_dir:
            rh_gitleaks.config.GITLEAKS_BIN_PATH = os.path.join(tmp_dir, "gitleaks")

            with open(rh_gitleaks.gitleaks_bin_path(), "rb") as gitleaks_bin:
                sha256sum = hashlib.sha256(gitleaks_bin.read())

            self.assertEqual(sha256sum.hexdigest(), download_sha256sum)

    @patch("subprocess.run")
    def test_run_gitleaks(self, mock_subprocess_run):
        """
        Confirm the subprocess is ran properly
        """
        with TemporaryDirectory() as tmp_dir:
            rh_gitleaks.config.PATTERNS_PATH = os.path.join(
                tmp_dir, "foo", "patterns.toml"
            )
            rh_gitleaks.config.GITLEAKS_BIN_PATH = os.path.join(
                tmp_dir, "bar", "gitleaks"
            )

            mock_subprocess_run.return_value.returncode = 0

            self.assertEqual(
                rh_gitleaks.run_gitleaks(["--help"]),
                0,
            )

            self.assertEqual(
                mock_subprocess_run.call_args[0][0],
                [
                    rh_gitleaks.config.GITLEAKS_BIN_PATH,
                    f"--config-path={rh_gitleaks.config.PATTERNS_PATH}",
                    "--help",
                ],
            )
