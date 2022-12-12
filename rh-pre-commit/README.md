# rh-pre-commit

This tool provides a standard set of [checks](#checks) as a single
[pre-commit hook](https://www.atlassian.com/git/tutorials/git-hooks)
for your project.

## Contents

[[_TOC_]]

## Requirements

You will need the following installed on your system:

* `python3`
* `pip`
* `make`

## Supported Operating Systems

* Linux (x86\_64)
* Mac (x86\_64)

Arm64 support for Mac is planned.

For additional OS support reach out to infosec@redhat.com.

## Uninstalling The Legacy Scripts

If you have the legacy bash versions of these scripts installed, you can use
[this script](../scripts/uninstall-legacy-tools) to locate and remove them. It
does not remove the symlinks created by the legacy enable-for script. The
`--force` option included in the install command below should replace any
legacy pre-commit symlinks under `--path`.

If you are unsure if you have the legacy versions of the script installed, you
can run the uninstall script to find out. It should only find and remove the
legacy scripts and will prompt you before doing so.

## Getting Started

**Quickstart**: If you are fine with all of the defaults here and with this
making changes to your existing repos, there is a [quickstart.sh](quickstart.sh)
that runs all of the commands from this section in one go. It's still good to
at least read through this section to have a better understanding of what the
tool does and what the quickstart accomplishes.

This section covers a default install. See the comments next to the commands
below for details about customizing the install, or if you don't want support
for managing multiple pre-commit hooks in one repo, check out the
[rh-multi-pre-commit vs rh-pre-commit](#rh-multi-pre-commit-vs-rh-pre-commit)
section.

Unless the
[changelog](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server#changelog)
says to, you will not need to run the configuration steps
again during an update.

At the end of this (assuming the defaults are applied):

* `rh-pre-commit`, `rh-multi-pre-commit`, `rh-gitleaks`, and `rh-gitleaks-gh-account` will be installed.
* You will have a global `~/.config/pre-commit/config.yaml` set up to enable rh-pre-commit
* The hook will be enabled for all the repos in your home dir
* The hook will be enabled by default for all new repos
* rh-gitleaks will be logged in and have a 2 year patterns server token

**Pull a fresh copy of the repo**

```sh
rm -rf /tmp/infosec-tools
git clone https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git /tmp/infosec-tools
# The rest of the commands assume you are in this subfolder of the repo
cd /tmp/infosec-tools/rh-pre-commit
```

**Install/Update the tools**

```sh
# If you need to install from a specific branch:
# git checkout <branch-name>

# (Recommended) Upgrade pip
python3 -m pip install --upgrade --user pip

# This installs the tools but you will still need to configure them
make install
```

**Configure the tools**

```sh
# To understand these options, run: python3 -m rh_pre_commit.multi configure --help
python3 -m rh_pre_commit.multi configure --configure-git-template --force
```

**Enable the hook in your existing repos**

```sh
# To understand these options, run: python3 -m rh_pre_commit.multi install --help
python3 -m rh_pre_commit.multi install --force --path ~/
```

And you should be all set!

**Confirming it works**

```sh
rm -rf /tmp/test-pre-commit && mkdir /tmp/test-pre-commit
cd /tmp/test-pre-commit
git init
echo 'secret="EdnBsJW59yS6bGxhXa5+KkgCr1HKFv5g"' > secret
git add secret &&
git commit
```

You should see an error containing lines like this:

```
...

INFO[0000] scan time: 476 microseconds
WARN[0000] leaks found: 1
ERROR: rh-gitleaks has detected sensitive information in your changes and will
not allow the commit to proceed.

If it the file does contain sensitive information, please remove it and try
your commit again.

If the detection was a false positive you can either add a gitleaks:allow
comment to the line to allow it or add a .gitleaks.toml in your repo's base
directory with the item added to the allowlist.

...
```

## Notifications About Updates

Please follow/subscribe-to the
[Pattern Distribution Server](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server).
doc in The Source. There is a change log at the bottom that is updated when
there are new releases.

## rh-multi-pre-commit vs rh-pre-commit

This repo actually provides two tools, rh-multi-pre-commit and rh-pre-commit.
rh-pre-commit is just the set of checks provided in this repo.
rh-multi-pre-commit extends [pre-commit.com](https://pre-commit.com) to
also check a config file at `~/.config/pre-commit/config.yaml`.

Any of the Getting Started steps that reference rh-multi-pre-commit should
also work with rh-pre-commit if you don't want support for multiple pre-commit
hooks in a repo.

## Usage

### Resetting Config

This section covers how to reset the config back to the defaults.

If you're using rh-multi-pre-commit:

```sh
# To understand these flags, run: python3 -m rh_pre_commit.multi configure --help
python3 -m rh_pre_commit.multi configure --configure-git-template --force
```

If you're using rh-pre-commit:

```sh
# To understand these flags, run: python3 -m rh_pre_commit configure --help
python3 -m rh_pre_commit configure --configure-git-template --force
```

### Enabling for Ad-Hoc Repos

This section covers how to enable the hook for an ad-hoc repo. You might
want to do this if you didn't run configure with `--configure-git-template`
set or want to swap out the hooks in a specific repo.

If you're using rh-multi-pre-commit:

```sh
# To understand these flags, run: python3 -m rh_pre_commit.multi install --help
python3 -m rh_pre_commit.multi install --force --path /path/to/repo
```

If you're using rh-pre-commit:

```sh
# To understand these flags, run: python3 -m rh_pre_commit install --help
python3 -m rh_pre_commit install --force --path /path/to/repo
```

### Ignoring False Leak Positives

The [Pattern Distribution Server Doc](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server#handling-false-positives)
has a section on how to handle false positives.

### Checks

These options allow you to turn on/off different checks provided by this
package without having to remove the entire hook.

#### Check Secrets (Default: On)

To turn it off a repo:

```sh
git config --bool rh-pre-commit.checkSecrets false
```

To turn it on a repo:

```sh
git config --bool rh-pre-commit.checkSecrets true
```

### Updating pre-commit.com style hooks

**NOTE:** This does not update the tools in this repo, this is like running
[pre-commit autoupdate](https://pre-commit.com/#updating-hooks-automatically)

To update the global pre-commit.com style hooks and the ones defined
in your project's current directory run:

```
python3 -m rh_pre_commit.multi update
```

This will list the config files it found and is running updates for.

## Troubleshooting

This section covers some basic troubleshooting steps. If you still need help,
please email infosec@redhat.com for assistance and provide a link to this
README for context.

### Command not found

If you run the command and get a `command not found` error, you can
reference the commands through their modules directly.

* `rh-gitleaks` becomes `python3 -m rh_gitleaks`
* `rh-gitleaks-gh-account` becomes `python3 -m rh_gitleaks.gh_account`
* `rh-pre-commit` becomes `python3 -m rh_pre_commit`
* `rh-multi-pre-commit` becomes `python3 -m rh_pre_commit.multi`

**For Mac users**, the CLI scripts are often installed under
`${HOME}/Library/Python/<some version>/bin`.

So say you you run `python3 --version` and see `Python 3.9.16`, then you would
add `${HOME}/Library/Python/3.9/bin` to your PATH in your `~/.zshrc` and then
source it.

Example (Assuming 3.9.x):

```sh
echo 'export PATH="${HOME}/Library/Python/3.11/bin:${PATH}"' >> ~/.zshrc
source ~/.zshrc
```

### Error Upgrading Pip Due To Missing CA Bundle

On a few older Linux systems, we've seen pip complain about not being able
to find the CA bundle. Setting the `REQUESTS_CA_BUNDLE` env variable to the
system's CA bundle was able to resolve it.

```sh
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-bundle.crt
python3 -m pip install --upgrade --user pip
```
