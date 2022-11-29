from unittest import TestCase
from unittest.mock import patch
from unittest.mock import Mock


from rh_gitleaks import gh_account


class GitHubAccountTest(TestCase):
    def test_parse_args(self):
        """
        Test the arg parser
        """

        args = gh_account.parse_args([])
        self.assertEqual(args.show_help, True)
        self.assertEqual(args.namespaces, [])

        args = gh_account.parse_args(["--help", "foo", "bar", "baz"])
        self.assertEqual(args.show_help, True)
        self.assertEqual(args.namespaces, [])

        args = gh_account.parse_args(["-h", "foo", "bar", "baz"])
        self.assertEqual(args.show_help, True)
        self.assertEqual(args.namespaces, [])

        args = gh_account.parse_args(["foo", "bar", "baz"])
        self.assertEqual(args.show_help, False)
        self.assertEqual(args.namespaces, ["foo", "bar", "baz"])

    def test_show_help(self):
        """
        Make sure it always returns an error status
        """
        self.assertNotEqual(gh_account.show_help(), 0)

    @patch("requests.get")
    @patch("rh_gitleaks.gh_account.run_gitleaks")
    def test_scan_namespaces(self, mock_run_gitleaks, mock_requests_get):
        # Setup and mock the env
        namespaces = ["foo", "bar", "baz"]
        mocks = []

        for ns in namespaces:
            mock = Mock()
            mock.json.return_value = [{"html_url": f"https://host/{ns}.git"}]
            mocks.append(mock)

        mock_requests_get.side_effect = mocks

        # Check that the proper calls were made to rh_gitleaks
        gh_account.scan_namespaces(["foo", "bar", "baz"])

        for i, call in enumerate(mock_run_gitleaks.call_args_list):
            args = call.args[0]
            ns = namespaces[i]
            self.assertEqual(args, ("-q", f"--repo-url=https://host/{ns}.git"))
