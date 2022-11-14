from argparse import ArgumentParser


def create_parser():
    parser = ArgumentParser(
        prog="rh-multi-pre-commit",
        description="Manage multiple pre-commit hooks for Red Hatters",
    )

    subparsers = parser.add_subparsers()

    install_parser = subparsers.add_parser(
        "install",
        help="Install the pre-commit hook in a project or projects",
    )
    install_parser.add_argument(
        "--check",
        action="store_true",
        help="Check to see where the hook would be installed, but don't install it",
    )
    install_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Check sub directories for git repos as well",
    )
    install_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing pre-commit hooks"
    )

    subparsers.add_parser(
        "configure", help="Configure the pre-commit hooks with the default config"
    )

    subparsers.add_parser(
        "login",
        help="Login to the pattern distribution server",
    )

    return parser


def main():
    create_parser().parse_args()
