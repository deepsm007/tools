#! /usr/bin/env bash
set -eo pipefail

print_usage() {
  echo "rh-multi-pre-commit quickstart script

WARNING

  This will apply rh-multi-pre-commit to every repo in your home dir
  (or repo(s) dir if specified) and overwrite any existing pre-commit hooks!

USAGE

  ./quickstart.sh -b=[branch] -r=[repos dir] -s

OPTIONS

  -b branch        (optional) which branch should be installed

  -r repo(s) dir   (required if no -f) a git repo(s) directory
                   (an absolute path or a path relative
                   to the current working directory)
                   to enable the tool in

  -s               (optional) include sign-off hook (Default: false)

  -f               (optional) force the script to run in the home directory \${HOME}

  -h               print this help message"
}


# Helpers
# =======
# Copied from https://github.com/thenets/rinted-container/blob/main/container/entrypoint.sh
if ! type tput >/dev/null 2>&1; then
    tput() {
        return 0
    }
fi

log_info() {
    local CYAN=$(tput setaf 6)
    local NC=$(tput sgr0)
    echo "${CYAN}[INFO]${NC} $*" 1>&2
}

log_warning() {
    local YELLOW=$(tput setaf 3)
    local NC=$(tput sgr0)
    echo "${YELLOW}[WARNING]${NC} $*" 1>&2
}

log_error() {
    local RED=$(tput setaf 1)
    local NC=$(tput sgr0)
    echo "${RED}[ERROR]${NC} $*" 1>&2
}

log_success() {
    local GREEN=$(tput setaf 2)
    local NC=$(tput sgr0)
    echo "${GREEN}[SUCCESS]${NC} $*" 1>&2
}

log_title() {
    local GREEN=$(tput setaf 2)
    local BOLD=$(tput bold)
    local NC=$(tput sgr0)
    echo 1>&2
    echo "${GREEN}${BOLD}---- $* ----${NC}" 1>&2
}

# Input validation
# ================
ORIGINAL_ARGS=("$@")

while getopts ":b:r:sfh" flag
do
  case "${flag}" in
    b) branch=${OPTARG};;
    r) repos_dir=${OPTARG};;
    s) signoff='True';;
    f) force_user_home='True';;
    h) print_usage; exit 0;;
    *) log_error "Invalid option: $1"; print_usage; exit 1;;
  esac
done

# Validate there's not command after the options
shift $((OPTIND-1))
for arg in "${@}"
do
  if [[ "${arg}" =~ ^- ]]
  then
    continue
  fi
  log_error "Invalid argument: ${arg}"
  log_error "Please use the following syntax:"
  print_usage
  exit 1
done

# If -f, then -r must be empty
if [[ -n "${force_user_home}" && -n "${repos_dir}" ]]
then
  log_error "Invalid arguments: -f and -r cannot be used together"
  print_usage
  exit 1
fi

# If -f
if [[ -n "${force_user_home}" ]]
then
  log_warning "Forcing the script to run in the home directory: ${HOME}"
  log_warning "All repos under ${HOME} will be affected!"
  log_warning ""
  log_warning "You can cancel this by pressing Ctrl+C"
  log_warning "The script will continue in 10 seconds..."
  sleep 10
  repos_dir="${HOME}"
fi

# If -r
if [[ -n "${repos_dir}" ]]
then
  # Ensure repos_dir is an absolute path
  if [[ "${repos_dir}" != /* ]]
  then
    repos_dir="${PWD}/${repos_dir}"
  fi

  # Ensure repos_dir is a directory
  if [[ ! -d "${repos_dir}" ]]
  then
    log_error "${repos_dir} is not a directory"
    exit 1
  fi
fi

# If no -f or -r, then fail
if [[ -z "${force_user_home}" && -z "${repos_dir}" ]]
then
  log_error "Invalid arguments: -f or -r must be used"
  print_usage
  exit 1
fi


# Main
# ====

# Start
log_title "rh-multi-pre-commit quickstart script"
log_info "Parameters"
log_info "  -b (branch): ${branch}"
log_info "  -r (repos dir): ${repos_dir}"
log_info "  -s (signoff): ${signoff}"
log_info "  -f (force user home): ${force_user_home}"
log_info "Applying rh-multi-pre-commit to all repos under:"
log_info "  ${repos_dir}"

set -xeo pipefail

# Pull a fresh copy of the repo
rm -rf /tmp/infosec-tools
set +e
git clone https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git /tmp/infosec-tools
if [[ $? -ne 0 ]]
then
  set +x
  log_error "Failed to clone the repo"
  log_error "Please check if you are connected to the VPN and authenticated using 'kinit'"
  exit 1
fi
set -e
cd /tmp/infosec-tools/rh-pre-commit

# Checkout a branch if it was specified
if [[ -n "${branch}" ]]
then
  git checkout "${branch}"
fi

# Upgrade pip
python3 -m pip install --upgrade --user pip

# Uninstall any legacy versions of the script if present
python3 ../scripts/uninstall-legacy-tools

# Install the tools
make install

# Configure it with the default settings
python3 -m rh_pre_commit.multi configure --configure-git-template --force

if [[ -n "${signoff}" ]]
then
  python3 -m rh_pre_commit.multi --hook-type commit-msg configure --force
fi

# Enable it for all existing projects under the home (or specified) directory
python3 -m rh_pre_commit.multi install --force --path "${repos_dir}"

if [[ -n "${signoff}" ]]
then
  python3 -m rh_pre_commit.multi --hook-type commit-msg install --force --path "${repos_dir}"
fi

set +x
log_success "Install complete!"
