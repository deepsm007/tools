#! /usr/bin/bash
#
# WARNING
#
#   This will apply rh-multi-pre-commit to every repo in your home dir and
#   overwrite any existing pre-commit hooks!
#
# USAGE
#
#   ./quickstart.sh [branch]
#
# OPTIONS
#
#   branch - (optional) which branch should be installed
#
set -xeo pipefail

# Pull a fresh copy of the repo
rm -rf /tmp/infosec-tools
git clone https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git /tmp/infosec-tools
cd /tmp/infosec-tools/rh-pre-commit

# Checkout a branch if it was specified
if [[ ! -z "$1" ]]
then
  git checkout $1
fi

# Upgrade pip
python3 -m pip install --upgrade --user pip

# Uninstall any legacy versions of the script if present
python3 ../scripts/uninstall-legacy-tools

# Install the tools
make install

# Configure it with the default settings
python3 -m rh_pre_commit.multi configure --configure-git-template --force

# Enable it for all existing projects under the home directory
python3 -m rh_pre_commit.multi install --force --path "${HOME}"
