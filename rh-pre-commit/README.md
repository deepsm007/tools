# rh-pre-commit

This tool provides a [pre-commit hook](https://www.atlassian.com/git/tutorials/git-hooks)
that runs a standard set of [tasks](#tasks) and a way to manage multiple
pre-commit hooks in your projects. The tool currently utilizes a pre-commit
hook for scanning for potential secrets and a commit-msg hook to provide an
attestation "sign off" in the commit message.

Rh-pre-commit currently provides two functions:

1. A check secrets task. This task utilizes gitleaks and internal patterns to
   identify potential secrets before they are committed. It requires the
   installation of a pre-commit hook in each git repository.

2. An optional sign-off task. This task provides an attestation in the commit
   message allowing teams to easily identify what version of the the hook was
   installed and what other tasks were enabled. It requires the installation of
   a commit-msg hook in each repository and for the check secrets task to be
   installed and enabled.

## Contents

[[_TOC_]]

## Requirements

You will need the following installed on your system:

* `python3` (Python 3.9 or higher)
* `pip`
* `make`

Your system will need to be connected to the Red Hat VPN during installation
and initial configuration.

If you are running RHEL 8,
[here is a guide](https://access.redhat.com/solutions/4763521)
for installing newer versions of Python. Make sure that `python3 --version`
returns the expected version. If it doesn't you may need to still set it via
the `alternatives --config python3` command.

## Supported Operating Systems

* Linux (x86\_64)
* Linux (arm64)
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

There are a number of different ways to install rh-pre-commit, the option you
choose will be determined by your requirements.

1. [Quickstart Install](#quickstart-install) - This is a common method for installing rh-pre-commit
   and its hooks in all your repositories.

2. [Manual Install](#manual-install) - Running the installation and configuration steps
   manually, including installing hooks.

3. [Pre-Commit-Config Install](#pre-commit-config-install) - If you already have pre-commit installed on your
   repo you can add this project to you `.pre-commit-config.yaml` file.

You can also check out the
[FAQ](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_concepts/rh_pre_commit_faq)
for more information about the tool.

## Installation & Updating

### Quickstart Install

Before starting the install make sure the [system requirements](#requirements)
are met.

If you are fine with a default install, there is a [quickstart.sh](quickstart.sh)
that runs all the commands from this section in one go. **Please still read
through the [Manual Install section](#manual-install)** to understand the
implications of the defaults applied by the quickstart and how apply updates!

If you need a custom install (for instance you don't want to override existing
hooks), you can run different commands via a [manual install](#manual-install).

**The quickstart will:**

* Set up the `@infosec-public/leaktk` internal copr repo if running on a
  supported dnf-enabled system. This allows you to get automatic future updates
  when doing dnf updates on the VPN.

* Install `rh-pre-commit`, `rh-multi-pre-commit`, `rh-gitleaks`,
  `rh-gitleaks-gl-account`, and `rh-gitleaks-gh-account`

* Set `rh-multi-pre-commit` as the pre-commit hook for all the repos under your
  home dir (overwriting any existing hooks due to the `--force` flag being set).

* Set `rh-multi-pre-commit` as the pre-commit hook by default for all new repos

* Create a `~/.config/pre-commit/config.yaml` config file for
  `rh-multi-pre-commit` to enable `rh-pre-commit`

* Configure `rh-gitleaks` with a 2-year Patterns Server auth token

* Disable `rh-multi-pre-commit` from automatically running local pre-commit
  hooks defined in a repositories `.pre-commit-config.yaml`.

**Supported Flags:**

* If the `-s` flag is set, it will repeat the above enabling a sign-off in the
  commit message using commit-msg hooks.

* You can use `-b` to specify a different branch (the default is `main`)

* You can use `-r` to specify which repos the hook should be installed in

* You can use `-f` to force the script to run in the entire `${HOME}` directory
  and install the hook in all git repos under it

**Examples:**

You don't have to run all of these, these are just here to explain how a few
flags work.

```sh
# This runs the quickstart against the main branch without enabling sign off
# and installs it in every repo under your home directory (i.e. the default):

./quickstart.sh -f

# This runs the quickstart against the main branch without enabling sign off
# and assumes your projects are under a `Workspace` directory:

./quickstart.sh -r ~/Workspace
```

And after you run the quickstart.sh, you should be all set! There is a
[section below](#testing-the-installation) that has steps for confirming
everything's working as expected.

### Manual Install

Before starting the install make sure the [system requirements](#requirements)
are met.

Unless the
[changelog](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_changelog/)
says to, you will not need to run the configuration steps
again during an update—just the steps up to and including `make install`.

**(Optional) RPM based install**

We have begun support for RPM based installs. The instructions for doing
an RPM based install can be found in [this guide](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_guides/leaktk_rpm_installation).
The guide also lists which systems we support. The RPM based install is already
covered in the quickstart.sh if your system supports it. If you've installed
the RPMs, you can skip to the **Configure the tools step** below.

**Pull a fresh copy of the repo**

```sh
cd "$(mktemp -d)"
git clone https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git
# The rest of the commands assume you are in this subfolder of the repo
cd ./tools/rh-pre-commit
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

Running the tool configuration performs the following:

1. It sets global git config settings used by the tooling.

2. When `--configure-git-template` is used it creates templates
   for the hooks so that all new git repositories to have hooks
   installed by default.

3. For `rh-multi-commit` it creates a global pre-commit configuration file.

```sh
# To understand these options, run: python3 -m rh_pre_commit.multi configure --help
python3 -m rh_pre_commit.multi configure --configure-git-template --force

# OPTIONAL: To configure commit-msg attestation (sign-off)
python3 -m rh_pre_commit.multi --hook-type commit-msg configure --force
```

**Install / Enable the hook in your existing repos**

```sh
# To understand these options, run: python3 -m rh_pre_commit.multi install --help
python3 -m rh_pre_commit.multi install --force --path ~/

# OPTIONAL: To install the commit-msg hook for commit message attestation (sign-off)
# If you don't want sign-off enabled for all repos under your home dir, you can
# provide a different path.
python3 -m rh_pre_commit.multi --hook-type commit-msg install --force --path ~/
```

And you should be all set! There is a [section below](#testing-the-installation)
that has steps for confirming everything's working as expected.

**Rh-multi-pre-commit considerations:**

In the context of `rh-pre-commit` we consider global configuration items those that
affect the behavior of all repositories. Local refers to configuration that affects
a single repository. This follows the `git config` convention, where the `--global`
flag is used to set values that affect all repositories.

`rh-multi-pre-commit` builds on [pre-commit.com](https://pre-commit.com/)'s
pre-commit framework to support a global config file in addition to hooks
defined in a project's local `.pre-commit-config.yaml`. Running local hooks
is disabled by default to avoid accidentally executing a malicious hook, but
it can be turned on per-repo or for all repos.

**Note:** If you don't want to support multiple pre-commit hooks per project
(the default), `rh-pre-commit` can be enabled instead. To do this, simply
replace `rh_pre_commit.multi` with `rh_pre_commit` in the steps above.

**Warning:** If you are using `rh-multi-pre-commit` with
`rh-pre-commit.enableLocalConfig = true`, in your git config, make sure you
trust the hooks defined in the repo's `.pre-commit-config.yaml`. It is disabled
by default to avoid executing a malicious hook.

**To enable running hooks defined in a repo's .pre-commit-config.yaml**

```sh
# Run from inside the repo you want to enable it on
git config --bool rh-pre-commit.enableLocalConfig true
```
**To enable running hooks defined in all repos' .pre-commit-config.yaml (use with caution)**

```sh
git config --bool --global rh-pre-commit.enableLocalConfig true
```

**Note:** The global setting is disabled every time you run `configure`

For more info see the
[rh-multi-pre-commit vs rh-pre-commit](#rh-multi-pre-commit-vs-rh-pre-commit)
section.

### Pre-Commit-Config Install

Before starting the install make sure the [system requirements](#requirements)
are met.

Also this set up assumes that you are using pre-commit.com's pre-commit hook
manager. Make sure you've followed their
[installation instructions](https://pre-commit.com/#install) including the
`pre-commit install` step in your repo first.

There are other ways to run
a local `.pre-commit-config.yaml` using this toolchain, but that's out of scope
for these specific instructions. For more information see
[this section of the FAQ](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_concepts/rh_pre_commit_faq#what-is-the-difference-between-rh-pre-commit-and-rh-multi-pre-commit-)

Rh-pre-commit can be configured directly in an existing `.pre-commit-config.yaml`
or by creating a new on in your repo as follows.

As `rh-pre-commit` is currently internal tooling it will only be able to install
when you are connected to the VPN. For external repositories this could be problematic,
so it is recommended that `rh-multi-pre-commit` is used instead. This allows you
to still run existing pre-commit hooks, as desired, whilst keeping the configuration
local.

Here is an example `.pre-commit-config.yaml`:

```yaml
---
repos:
  - repo: https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git
    rev: rh-pre-commit-2.2.0
    hooks:
      # If you have not run this hook on your system before, it may prompt you to
      # log in for patterns, and you will need to try again.
      #
      # Docs: https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_components/rh_pre_commit
      - id: rh-pre-commit
      # - id: rh-pre-commit.commit-msg # Optional for commit-msg attestation
```

For updates, follow the
[leaktk changelog](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_changelog/).

**Note:** For this method to work, you will need to [install pre-commit](https://pre-commit.com/#install)
and the relevant hooks in your repo. `rh-pre-commit` requires pre-commit's `pre-commit`
hook to be installed, and `rh-pre-commit.commit-msg` requires pre-commit's `commit-msg`
hook to be installed. (This also works with rh-multi-pre-commit with local config
enabled for the repo. It just may run the checks twice if you're running it through
rh-multi-pre-commit.)

### Non-Interactive Install

For a non-interactive install you can set the auth token manually or through an
environment variable instead of using `rh-gitleaks login`. The `configure` step
detects that rh-gitleaks is already logged in and won't prompt for a token.

Steps:

1. Configure the [Pattern Server Auth Token](../rh-gitleaks#pattern-server-auth-token)
2. Follow the steps in one of the instillation sections above.

### Testing the Installation

This applies to the quickstart and manual steps, but a slightly modified
version of this could still work in a repo containing a .pre-commit-config.yaml

```sh
cd "$(mktemp -d)"
git init
echo 'secret="EdnBsJW59yS6bGxhXa5+KkgCr1HKFv5g"' > secret
git add secret
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

## FAQ

You can also check out the
[FAQ](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_concepts/rh_pre_commit_faq)
for more information about the tool.

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
a commit. It will run them during a commit only if
`rh-pre-commit.enableLocalConfig` is set to `true` in your git config.

If you don't want to use the `rh-multi-pre-commit` manager, any of the installation
steps that reference `rh_pre_commit.multi` should also work with `rh_pre_commit`.
You can also switch between the two by running the install steps again, using the one you
want to enable.


## Usage

### Resetting Config

This section covers how to reset the config back to the defaults. There are
different commands for pre-commit and commit-msg hooks to enable `rh-pre-commit`
to run at different stages of the git commit process.

If you're using rh-multi-pre-commit:
```sh
# To understand these flags, run: python3 -m rh_pre_commit.multi configure --help
python3 -m rh_pre_commit.multi configure --configure-git-template --force

# OPTIONAL: To reset commit-msg attestation configuration
python3 -m rh_pre_commit.multi --hook-type commit-msg configure --configure-git-template --force
```

If you're using rh-pre-commit:
```sh
# To understand these flags, run: python3 -m rh_pre_commit configure --help
python3 -m rh_pre_commit configure --configure-git-template --force

# OPTIONAL: To reset commit-msg attestation configuration
python3 -m rh_pre_commit --hook-type commit-msg configure --configure-git-template --force
```

### Enabling for Ad-Hoc Repos

This section covers how to enable the hook for an ad-hoc repo. You might
want to do this if you didn't run configure with `--configure-git-template`
set or want to swap out the hooks in a specific repo.

If you're using rh-multi-pre-commit:
```sh
# To understand these flags, run: python3 -m rh_pre_commit.multi install --help
python3 -m rh_pre_commit.multi install --force --path /path/to/repo

# OPTIONAL: To install commit-msg attestation hook
python3 -m rh_pre_commit.multi --hook-type commit-msg install --force --path /path/to/repo
```

If you're using rh-pre-commit:
```sh
# To understand these flags, run: python3 -m rh_pre_commit install --help
python3 -m rh_pre_commit install --force --path /path/to/repo

# OPTIONAL: To install commit-msg attestation hook
python3 -m rh_pre_commit --hook-type commit-msg install --force --path /path/to/repo
```

### Ignoring False Leak Positives

The [Pattern Server Doc](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server#handling-false-positives)
has a section on how to handle false positives.

## Tasks

These options allow you to turn on/off different tasks run by this
package without having to remove the entire hook.

#### Check Secrets (Default: On)

This task scans the repository on pre-commit for any potential secrets.

To turn it off a repo:

```sh
git config --bool rh-pre-commit.checkSecrets false
```

To turn it on a repo:

```sh
git config --bool rh-pre-commit.checkSecrets true
```

#### SignOff (Default: On)

This task signs off on a commit message attesting that the hook is
installed and enabled.

To turn it off for a repo:

```sh
git config --bool rh-pre-commit.commit-msg.signOff false
```

To turn it on for a repo:

```sh
git config --bool rh-pre-commit.commit-msg.signOff true
```

The output of this task is appended to the COMMIT-MSG during commit, and looks
like the following:
```
    rh-pre-commit.version: 2.2.0
    rh-pre-commit.check-secrets: ENABLED
```

### Updating pre-commit.com style hooks

**Note:** This does not update the tools in this repo, this is like running
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

### Using an editor/IDE inside a Flatpak

If your editor is running from a Flatpak and you use its built in features for
doing git commits, you may run into issues where it can't find the rh-pre-commit
Python package.

Note: We've not experimented with troubleshooting this situation in depth
so it may take some trial and error to get it right. You are welcome to
contact us for [support](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_guides/support)
and we'll include the lessons learned in this section. Also the steps may
be different depending which editor your using.

Unverified solution:

You may be able to resolve the issue by using something like Flatseal to give
the app access to the directory where the package is installed.

You can figure out where the package is installed by running:

```
python3 -c 'import rh_pre_commit; print(rh_pre_commit.__path__)'
```

### Installing on MacOS <14

When attempting to install on older versions MacOS you may run into errors like
below:
```
INFO: pip is looking at multiple versions of rh-pre-commit to determine which version is compatible with other requirements. This could take a while.
ERROR: Ignored the following versions that require a different python version: 3.0.0 Requires-Python >=3.8; 3.0.1 Requires-Python >=3.8; 3.0.2 Requires-Python >=3.8; 3.0.3 Requires-Python >=3.8; 3.0.4 Requires-Python >=3.8; 3.1.0 Requires-Python >=3.8; 3.1.1 Requires-Python >=3.8; 3.2.0 Requires-Python >=3.8; 3.2.1 Requires-Python >=3.8; 3.2.2 Requires-Python >=3.8; 3.3.0 Requires-Python >=3.8; 3.3.1 Requires-Python >=3.8; 3.3.2 Requires-Python >=3.8; 3.3.3 Requires-Python >=3.8; 3.4.0 Requires-Python >=3.8; 3.5.0 Requires-Python >=3.8
ERROR: Could not find a version that satisfies the requirement pre-commit>=3.2.0 (from rh-pre-commit) (from versions: ...)
ERROR: No matching distribution found for pre-commit>=3.2.0
```

This is normally caused by the version of python shipped with older MacOS
versions as it does not meet pre-commit requirements. Python >=3.8 is a minimum
requirement for the version of pre-commit rh-pre-commit requires. The
following instructions should resolve the issue:
1. Install [Homebrew](https://github.com/Homebrew/brew/releases/), commonly referred to as brew.
2. Use brew to install python `brew install python@3.11`
3. Set the new python as the system default
`brew link --overwrite python@3.11`
4. Add the users python bin to `PATH`, by adding something similar to the
following to your shell configuration file
`export PATH=PATH:/Users/<user>/Library/Python/3.11/bin`
