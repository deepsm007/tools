from unittest import TestCase

from rh_pre_commit import multi


class MultiPreCommitHookTest(TestCase):
    def test_create_parser(self):
        """
        Simply spot check the arg parser
        """
        parser = multi.create_parser()
        self.assertEqual(parser.prog, "rh-multi-pre-commit")

        # Test install args because we don't want to mess these up
        tests = [
            ("--check --force --recursive", True, True, True),
            ("--force --recursive", False, True, True),
            ("--check --recursive", True, False, True),
            ("--check", True, False, False),
            ("", False, False, False),
        ]

        for args, check, force, recursive in tests:
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
            self.assertEqual(
                ns.recursive,
                recursive,
                f"recursive: {ns.recursive} != {recursive} for {args}",
            )
