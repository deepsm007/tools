import os

from argparse import Namespace
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from rh_pre_commit import common
from rh_pre_commit import templates
from src.rh_pre_commit import git

PRE_COMMIT_CONFIG_YAML = """
---
repos:
  - repo: https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git
    rev: main
    hooks:
      - id: rh-pre-commit
      - id: rh-pre-commit.commit-msg

  #
  # Include some malformed ones to make sure that's covered
  #

  # Some other empty repo
  - repo: https://example.com

  # Not valid at all
  - foo: bar

  # Our repo but no hooks
  - repo: https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git

  # Our repo but malformed hooks
  - repo: https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git
    hooks:
      - foo: bar
"""


class CommonTest(TestCase):
    hook_types = list(templates.RH_PRE_COMMIT_HOOKS)

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=R1732

        # In CICD the git user is not configured - this will only set it up if user.name is empty
        if not git.config("user.name", flags=["global"]).stdout.decode("UTF-8").strip():
            git.config("user.name", "rh-pre-commit-test", ["global"])
            git.config(
                "user.email", "infosec-alerts+rh-pre-commit-test@redhat.com", ["global"]
            )

        test_submod = "test-submodule"
        test_worktree = "test-worktree"

        deep_repo_path = os.path.join(self.tmp_dir.name, "foo", "bar", "baz")
        wt_main_repo_path = os.path.join(self.tmp_dir.name, "wt-test")
        test_repo_path = os.path.join(self.tmp_dir.name, "test")
        repo_for_submod_path = os.path.join(self.tmp_dir.name, test_submod)
        self.repo_for_worktree_path = os.path.join(
            self.tmp_dir.name, test_worktree, ".git"
        )

        # Create and init normal git repositories, including adding files, so they are not empty
        self.expected = [
            deep_repo_path,
            wt_main_repo_path,
            test_repo_path,
            repo_for_submod_path,
        ]
        for i, d in enumerate(self.expected):
            os.makedirs(d)
            git.run("init", "--template=", cwd=d)
            with open(d + "/1", "w", encoding="UTF-8") as f:
                f.write("Contents")
            git.run(*["add", "-A"], cwd=d)
            git.run(*["commit", "--no-gpg-sign", "-m", "message"], cwd=d)
            self.expected[i] = os.path.join(d, ".git")

        # Create a submodule
        self.submodule_repo_path = os.path.join(
            test_repo_path, ".git", "modules", test_submod
        )
        self.expected.append(self.submodule_repo_path)

        git.run(
            *[
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "../" + test_submod,
            ],
            cwd=test_repo_path,
        )

        git.run(
            *[
                "-c",
                "protocol.file.allow=always",
                "worktree",
                "add",
                "-b",
                "worktree",
                "../" + test_worktree,
            ],
            cwd=wt_main_repo_path,
        )
        # We will expect this repository to be found twice as a worktree points back to its
        # parent git repository folder.
        self.expected.append(os.path.join(wt_main_repo_path, ".git"))

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_create_parser(self):
        """
        Simply spot check the arg parser
        """
        parser = common.create_parser("foo-bar-baz")
        self.assertEqual(parser.prog, "foo-bar-baz")

        # Test install args because we really don't want to mess these up
        install_tests = (
            ("--check --force", True, True, "."),
            ("--force", False, True, "."),
            ("--check", True, False, "."),
            ("--check --force --path foo", True, True, "foo"),
            ("--force --path=bar", False, True, "bar"),
            ("--check --path baz", True, False, "baz"),
            ("", False, False, "."),
        )
        for hook_type in self.hook_types:
            for args, check, force, path in install_tests:
                ns = parser.parse_args(
                    [f"--hook-type={hook_type}", "install", *args.split()]
                )
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
                    ns.path,
                    path,
                    f"path: {ns.path} != {path} for {args}",
                )

        # Test configure args
        configure_tests = (
            ("--configure-git-template", True, False),
            ("--configure-git-template --force", True, True),
            ("", False, False),
        )

        for args, configure_git_template, force in configure_tests:
            ns = parser.parse_args(["configure", *args.split()])
            self.assertEqual(
                ns.configure_git_template,
                configure_git_template,
                f"check: {ns.configure_git_template} != {configure_git_template} for {args}",
            )
            self.assertEqual(
                ns.force,
                force,
                f"check: {ns.force} != {force} for {args}",
            )

    def test_find_repos(self):
        """
        Find repos under a given structure
        """
        # On Mac /var/folders is under /private/var/folders git links the full address, so
        # we strip it to match what we are creating.
        mac_private_tmp = "/private"
        common_dirs = list(common.find_repos(self.tmp_dir.name))
        for i, d in enumerate(common_dirs):
            if d.startswith(mac_private_tmp):
                common_dirs[i] = d[len(mac_private_tmp) :]

        self.assertEqual(sorted(self.expected), sorted(common_dirs))

    @patch("logging.info")
    @patch("rh_pre_commit.common.find_repos")
    def test_list_repos(self, mock_find_repos, mock_logging_info):
        repos = [
            "/home/user/repo/.git/modules/foo",
            "/home/user/repo/.git",
        ]

        mock_find_repos.return_value = repos

        common.list_repos(Namespace(path="/home/user"))

        for i, repo in enumerate(sorted(repos)):
            call = mock_logging_info.call_args_list[i]

            # Check the path
            self.assertEqual(call.args[1], repo)

    def test_hook_installed_git_folder(self):
        hook_type = "pre-commit"

        # It should work with a regular git directory
        with TemporaryDirectory() as tmp_dir:
            args = Namespace(hook_type=hook_type, force=True, path=tmp_dir)
            repo_path = os.path.join(tmp_dir, ".git")
            hook_dir = os.path.join(repo_path, "hooks")
            hook_path = os.path.join(hook_dir, hook_type)
            config_path = os.path.join(tmp_dir, ".pre-commit-config.yaml")

            # Just to make sure we're starting off clean
            os.makedirs(hook_dir)
            self.assertFalse(os.path.isfile(hook_path))

            # If it doesn't exist it should fail
            self.assertFalse(common.hook_installed(hook_type, repo_path))

            # It isn't executable nor does it have the right content
            with open(hook_path, "w", encoding="UTF-8") as hook_file:
                hook_file.write("foo")

            self.assertFalse(common.hook_installed(hook_type, repo_path))

            # It has to be the right content
            common.install(args, "bar")
            self.assertFalse(common.hook_installed(hook_type, repo_path))

            # If it contains rh-pre-commit it's good
            status = common.install(args, templates.RH_PRE_COMMIT_HOOKS[hook_type])
            self.assertEqual(status, 0)
            self.assertTrue(common.hook_installed(hook_type, repo_path))

            # If it contains rh-multi-pre-commit it's good
            status = common.install(
                args, templates.RH_MULTI_PRE_COMMIT_HOOKS[hook_type]
            )
            self.assertEqual(status, 0)
            self.assertTrue(common.hook_installed(hook_type, repo_path))

            # If it just contains pre-commit then it's not valid
            status = common.install(args, "exec pre-commit")
            self.assertEqual(status, 0)
            self.assertFalse(common.hook_installed(hook_type, repo_path))

            # If pre-commit is configured to run the hook it's valid
            with open(config_path, "w", encoding="UTF-8") as config_file:
                config_file.write(PRE_COMMIT_CONFIG_YAML)

            status = common.install(args, "exec pre-commit")
            self.assertEqual(status, 0)
            self.assertTrue(common.hook_installed(hook_type, repo_path))

    def test_hook_installed_git_file(self):
        hook_type = "pre-commit"

        args = Namespace(hook_type=hook_type, force=True, path=self.tmp_dir.name)

        # Submodule - It has to be the right content
        common.install(args, "bar")
        self.assertFalse(common.hook_installed(hook_type, self.submodule_repo_path))
        # Worktree - It has to be the right content
        common.install(args, "bar")
        self.assertFalse(common.hook_installed(hook_type, self.repo_for_worktree_path))

        # Submodule - If it contains rh-pre-commit it's good
        status = common.install(args, templates.RH_PRE_COMMIT_HOOKS[hook_type])
        self.assertEqual(status, 0)
        self.assertTrue(common.hook_installed(hook_type, self.submodule_repo_path))

        # Worktree - If it contains rh-pre-commit it's good
        status = common.install(args, templates.RH_PRE_COMMIT_HOOKS[hook_type])
        self.assertEqual(status, 0)
        self.assertTrue(common.hook_installed(hook_type, self.repo_for_worktree_path))
