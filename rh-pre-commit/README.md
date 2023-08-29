# rh-pre-commit

This tool provides a [pre-commit hook](https://www.atlassian.com/git/tutorials/git-hooks)
that runs a standard set of [checks](#checks) and a way to manage multiple
pre-commit hooks in your projects.

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
* Mac (arm64)

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

**Quickstart:**

If you are fine with a default install, there is a [quickstart.sh](quickstart.sh)
that runs all of the commands from this section in one go. **Please still read
through this section** to understand the implications of the defaults applied
by the quickstart!

**A default install will:**

* Install `rh-pre-commit`, `rh-multi-pre-commit`, `rh-gitleaks`, and `rh-gitleaks-gh-account`
* Set `rh-multi-pre-commit` as the pre-commit hook for all the repos under your home dir
* Set `rh-multi-pre-commit` as the pre-commit hook by default for all new repos
* Create a `~/.config/pre-commit/config.yaml` config file for `rh-multi-pre-commit` to enable `rh-pre-commit`
* Configure `rh-gitleaks` with a 2 year patterns server token

**Rh-multi-pre-commit considerations:**

`rh-multi-pre-commit` builds on [pre-commit.com](https://pre-commit.com/)'s
pre-commit framework to support a global config file in addition to hooks
defined in a project's `.pre-commit-config.yaml`. If you don't want to support
multiple pre-commit hooks per project (the default), `rh-pre-commit` can be
enabled instead.

**Warning:** If you are using `rh-multi-pre-commit`, make sure you trust the
pre-commit hooks defined in a project's `.pre-commit-config.yaml` before making
a commit. It will run them during a commit.

For more info see the
[rh-multi-pre-commit vs rh-pre-commit](#rh-multi-pre-commit-vs-rh-pre-commit)
section.

**Updating:**

Unless the
[changelog](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_changelog/)
says to, you will not need to run the configuration steps
again during an update—just the steps up to and including `make install`.

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

If it the file contains sensitive information, please remove it and try
your commit again.

If the detection was a false positive, the documentation[1] contains a section
for handling false positives.

[1] https://patterns.security.redhat.com/docs

```

## Notifications About Updates

Please follow the
[LeakTK Changelog blog](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_changelog/)
for all important updates.

## rh-multi-pre-commit vs rh-pre-commit

`rh-multi-pre-commit` provides a way for teams to install multiple pre-commit
hooks in their projects. Teams that already have a good pre-commit hook
management tool can leverage `rh-pre-commit` without `rh-multi-pre-commit`, but
`rh-multi-pre-commit` is a supported solution for the folks who need it.

**So why extend an existing tool?**

[Pre-commit.com](https://pre-commit.com/)'s framework does 99% of what we want
except it doesn't support the ability to have a global config file (and they
were opposed to that feature being added to the upstream project). So
`rh-multi-pre-commit` leverages the nifty features from pre-commit.com (like
per-project `.pre-commit-config.yaml`s while also supporting the option to have
global config.

A global config file is needed so that we can continue leveraging internal
tools even when working on upstream, open-source projects where all of the
contributors might not have access to the internal tooling but the project
might have its own pre-commit requirements. Basically we are trying to avoid
the situation where someone has to choose between enabling our pre-commit hook
or enabling one required by their team or community.

The global config file is at `~/.config/pre-commit/config.yaml` and created/reset
by the `rh-multi-pre-commit configure` command.

**Warning:** If you are using `rh-multi-pre-commit`, make sure you trust the
pre-commit hooks defined in a project's `.pre-commit-config.yaml` before making
a commit. It will run them during a commit.

If you often contribute to untrusted projects and/or don't want to use the
`rh-multi-pre-commit` manager, any of the Getting Started steps that reference
`rh-multi-pre-commit` should also work with `rh-pre-commit`. You can also
switch between the two by running the install steps again, using the one you
want to enable.

There are plans to provide an option for telling `rh-multi-pre-commit` to use
global config only, project-config only, or both project and local config.
(More details will come when the feature's released).


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

The [Pattern Server Doc](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server#handling-false-positives)
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

### Command Not Found

If you get a `command not found` error and you know the scripts were installed,
it's likely that the place the scripts were installed is not on your path.

When you run `make install`, you may see a warning like this towards the end:

```
WARNING: The scripts rh-gitleaks and rh-gitleaks-gh-account are installed in '/home/user/.local/bin' which is not on PATH.
Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.`
```

If you add the directory from the warning you saw to your PATH (this will be
different than the one in the example above), that should resolve the problem.
If you're not sure what it means to "add a directory to your path", a quick
search online should provide some examples to help you get set up.

Alternatively, you can reference the commands through their modules directly:

* `rh-gitleaks` becomes `python3 -m rh_gitleaks`
* `rh-gitleaks-gh-account` becomes `python3 -m rh_gitleaks.gh_account`
* `rh-pre-commit` becomes `python3 -m rh_pre_commit`
* `rh-multi-pre-commit` becomes `python3 -m rh_pre_commit.multi`

### Error Upgrading Pip Due To Missing CA Bundle

On a few older Linux systems, we've seen pip complain about not being able
to find the CA bundle. Setting the `REQUESTS_CA_BUNDLE` env variable to the
system's CA bundle was able to resolve it.

```sh
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-bundle.crt
python3 -m pip install --upgrade --user pip
```
