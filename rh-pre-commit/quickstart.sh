#! /usr/bin/bash
set -xeuo pipefail

#
# WARNING: This will apply rh-multi-pre-commit to every
# repo in your home dir and overwrite any existing pre-commit
# hooks
#

# Pull a fresh copy of the repo
rm -rf /tmp/infosec-tools
git clone https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git /tmp/infosec-tools
cd /tmp/infosec-tools/rh-pre-commit

# Install and configure the tools with the default settings
make install
rh-multi-pre-commit configure --configure-git-template --force
rh-multi-pre-commit install --force --path ~/
