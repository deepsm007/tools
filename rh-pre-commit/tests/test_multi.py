import os

from tempfile import TemporaryDirectory
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

    def test_find_repos(self):
        """
        Find repos under a given structure
        """
        with TemporaryDirectory() as tmp_dir:
            expected = [
                os.path.join(tmp_dir, "foo", "bar", "baz", ".git"),
                os.path.join(tmp_dir, ".git"),
                os.path.join(tmp_dir, "test", ".git"),
            ]

            for d in expected:
                os.makedirs(d)
                os.makedirs(d + "-not-git")

            # Have a file named .git
            file_test = os.path.join(tmp_dir, "git-file")
            modfile = os.path.join(file_test, ".git")

            os.makedirs(file_test)
            with open(modfile, "w", encoding="UTF-8") as module:
                module.write("gitdir: ../.git/modules/git-file")

            expected.append(os.path.join(file_test, "../.git/modules/git-file"))

            self.assertEqual(sorted(expected), sorted(multi.find_repos(tmp_dir)))
