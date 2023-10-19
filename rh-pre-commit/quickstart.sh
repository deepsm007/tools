#! /usr/bin/env bash
#
# WARNING
#
#   This will apply rh-multi-pre-commit to every repo in your home dir
#   (or repo(s) dir if specified) and overwrite any existing pre-commit hooks!
#
# USAGE
#
#   ./quickstart.sh -b=[branch] -r=[repos dir] -s
#
# OPTIONS
#
#   -b branch - (optional) which branch should be installed
#   -r git repo(s) dir - (optional) a git repo(s) directory
#                        (an absolute path or a path relative
#                        to the current working directory)
#                        to enable the tool in (Default: $HOME)
#   -s - (optional) include sign-off hook (Default: false)
#
set -xeo pipefail

while getopts b:r:s flag
do
  case "${flag}" in
    b) branch=${OPTARG};;
    r) repos_dir=${OPTARG};;
    s) signoff=True;;
    *) echo "Invalid option."; head -n 17 "$0"; exit 1;;
  esac
done

if [[ -n "$repos_dir" ]]
then
  if [[ "${repos_dir}" != /* ]]
  # $repos_dir is not an absolute path
  then
    repos_dir="${PWD}/${repos_dir}"
  fi
else # No '-r repo(s) dir' specified, use $HOME
  repos_dir="${HOME}"
fi
if [[ ! -d "${repos_dir}" ]]
then
  echo "${repos_dir} is not a directory"
  exit 1
fi

# Pull a fresh copy of the repo
rm -rf /tmp/infosec-tools
git clone https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git /tmp/infosec-tools
cd /tmp/infosec-tools/rh-pre-commit

# Checkout a branch if it was specified
if [[ -n "$branch" ]]
then
  git checkout "$branch"
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

# Enable it for all existing projects under the home (or specified) directory
python3 -m rh_pre_commit.multi install --force --path "${repos_dir}"

if [[ -n "$signoff" ]]
then
  python3 -m rh_pre_commit.multi --hook-type commit-msg install --force --path "${repos_dir}"
fi
