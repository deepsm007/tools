import os
import hashlib

from datetime import datetime
from unittest import TestCase
from unittest.mock import patch
from tempfile import TemporaryDirectory

import jwt
import rh_gitleaks


class RHGitleaksTest(TestCase):
    mock_resp = b"mock"
    mock_sha256sum = hashlib.sha256(mock_resp).hexdigest()

    mock_token = jwt.encode(
        {
            "iss": "pattern-distribution-server-mock",
            "exp": int(datetime.utcnow().timestamp()) + 5000,
        },
        key="mock",
    )

    def test_parse_args(self):
        tests = (
            # Configure should ignore anything that isn't configure
            (
                ["configure", "--foo"],
                {
                    "gitleaks": [],
                    "rh_gitleaks": ["configure"],
                },
            ),
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

    @patch("requests.get")
    def test_gitleaks_bin_path(self, mock_requests_get):
        """
        Make sure it pulls and validates a version of gitleaks
        """
        mock_requests_get.return_value.content = self.mock_resp
        rh_gitleaks.config.GITLEAKS_BIN_DOWNLOAD_SHA256SUM = self.mock_sha256sum

        with TemporaryDirectory() as tmp_dir:
            rh_gitleaks.config.GITLEAKS_BIN_PATH = os.path.join(tmp_dir, "gitleaks")

            with open(rh_gitleaks.gitleaks_bin_path(), "rb") as gitleaks_bin:
                sha256sum = hashlib.sha256(gitleaks_bin.read())

            self.assertEqual(sha256sum.hexdigest(), self.mock_sha256sum)

    @patch("requests.get")
    @patch("subprocess.run")
    def test_run_gitleaks(self, mock_subprocess_run, mock_requests_get):
        """
        Confirm the subprocess is ran properly
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_requests_get.return_value.content = self.mock_resp
        rh_gitleaks.config.GITLEAKS_BIN_DOWNLOAD_SHA256SUM = self.mock_sha256sum

        with TemporaryDirectory() as tmp_dir:
            # The extra dir in the middle is to confirm it will be created
            # if it doesn't exist
            rh_gitleaks.config.PATTERNS_PATH = os.path.join(
                tmp_dir, "a", "patterns.toml"
            )
            rh_gitleaks.config.GITLEAKS_BIN_PATH = os.path.join(
                tmp_dir, "b", "gitleaks"
            )
            rh_gitleaks.config.PATTERNS_AUTH_JWT_PATH = os.path.join(
                tmp_dir, "c", "auth.jwt"
            )

            # Check the results of a configure and run
            self.assertEqual(rh_gitleaks.configure(auth_jwt=self.mock_token), 0)
            self.assertEqual(rh_gitleaks.run_gitleaks(["--help"]), 0)
            self.assertEqual(
                mock_subprocess_run.call_args[0][0],
                [
                    rh_gitleaks.config.GITLEAKS_BIN_PATH,
                    f"--config-path={rh_gitleaks.config.PATTERNS_PATH}",
                    "--help",
                ],
            )
