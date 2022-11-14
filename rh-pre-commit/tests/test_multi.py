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
            ("--check --force", True, True),
            ("--force", False, True),
            ("--check", True, False),
            ("--check", True, False),
            ("", False, False),
        ]

        for args, check, force in tests:
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

    def test_find_repos(self):
        """
        Find repos under a given structure
        """
        with TemporaryDirectory() as tmp_dir:
            expected = [
                ("R", os.path.join(tmp_dir, "foo", "bar", "baz", ".git")),
                ("R", os.path.join(tmp_dir, ".git")),
                ("R", os.path.join(tmp_dir, "test", ".git")),
            ]

            for d in expected:
                os.makedirs(d[1])
                os.makedirs(d[1] + "-not-git")

            # Have a file named .git
            file_test = os.path.join(tmp_dir, "git-file")
            modfile = os.path.join(file_test, ".git")

            os.makedirs(file_test)
            with open(modfile, "w", encoding="UTF-8") as module:
                module.write("gitdir: ../.git/modules/git-file")

            expected.append(("M", os.path.join(file_test, "../.git/modules/git-file")))

            self.assertEqual(sorted(expected), sorted(multi.find_repos(tmp_dir)))
