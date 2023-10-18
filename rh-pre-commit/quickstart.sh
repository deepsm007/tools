#! /usr/bin/env bash
#
# WARNING
#
#   This will apply rh-multi-pre-commit to every repo in your home dir and
#   overwrite any existing pre-commit hooks!
#
# USAGE
#
#   ./quickstart.sh -b=[branch] -s
#
# OPTIONS
#
#   -b branch - (optional) which branch should be installed
#   -s - (optional) include sign-off hook (Default: false)
#
set -xeo pipefail

while getopts b:s flag
do
  case "${flag}" in
    b) branch=${OPTARG};;
    s) signoff=True;;
    *) echo "Invalid option."; head -n 17 "$0"; exit 1;;
  esac
done

# Pull a fresh copy of the repo
rm -rf /tmp/infosec-tools
git clone https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git /tmp/infosec-tools
cd /tmp/infosec-tools/rh-pre-commit

# Checkout a branch if it was specified
if [[ -n "$branch" ]]
then
  git checkout $branch
fi

# Upgrade pip
python3 -m pip install --upgrade --user pip

# Uninstall any legacy versions of the script if present
python3 ../scripts/uninstall-legacy-tools

# Install the tools
make install

# Configure it with the default settings
python3 -m rh_pre_commit.multi configure --configure-git-template --force

if [[ -n "$signoff" ]]
then
  python3 -m rh_pre_commit.multi --hook-type commit-msg configure --force
fi

# Enable it for all existing projects under the home directory
python3 -m rh_pre_commit.multi install --force --path "${HOME}"

if [[ -n "$signoff" ]]
then
  python3 -m rh_pre_commit.multi --hook-type commit-msg install --force --path "${HOME}"
fi
