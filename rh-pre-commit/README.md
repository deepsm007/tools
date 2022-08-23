# rh-pre-commit

A set of standard pre-commit hooks to run on your projects.

## Contents

[[_TOC_]]

## Supported Operating Systems

* Linux (amd64)
* [WIP] Darwin (amd64)

For additional OS support reach out to infosec@redhat.com

## Updates

Please subscribe to the [patterns server user guide](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server)
for information about changes.

The installing and updating section below covers how to update the CLI tool if
there's been a change.

## Installing and Updating

The quickstart below covers how to do a full initial install and set up access
to the patterns server.

Go to the folder where you want to clone this repo

```sh
cd ~/
```

Clone the repo (if the repo is already cloned, do a `git pull` from inside the repo instead)

```sh
git clone https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git infosec-dev-tools
```

Go to the `rh-pre-commit` folder

```
cd ./infosec-dev-tools/rh-pre-commit/
```

Install the hooks (if doing an update, stop after this step)

If you don't have sudo access on your system, see "Advanced Options" below.

```sh
sudo make install
```

Install pre-commit (Fedora)

```sh
sudo dnf install -y pre-commit
```

Install pre-commit (Other OS)

Follow [pre-commit's instructions](https://pre-commit.com/#install)
for other ways to install.

Configure rh-multi-pre-commit

```sh
mkdir -p ~/.config/pre-commit/
cp ./etc/pre-commit/config.yaml ~/.config/pre-commit/config.yaml
```

Make the hooks the default for all new repos (cloned or created).

```sh
git config --global init.templateDir ~/.git-template
mkdir -p ~/.git-template/hooks && ln -snf $(which rh-multi-pre-commit) ~/.git-template/hooks/pre-commit
```

Configure the patterns server

```sh
mkdir -p ~/.config/rh-gitleaks
```

* Go to https://patterns.security.redhat.com/token
* Copy the token and put it at ~/.config/rh-gitleaks/auth.jwt

Confirm you see the help options and no errors

```sh
rh-gitleaks --help
```

Set up the hook for existing projects

```sh
# (Optional but recommended) run this to see what changes the following command
# will make and review the output to make sure there's nothing unexpected
# there. If there is, you can change the `~/` part of these commands to be the
# path to where you keep your projects and test again until you're happy with
# the output. Then, you can run the following command (i.e. the one with
# `bash -c` instead of `echo`), changing `~/`, to enable the hook in
# those existing repos.
find ~/ -name .git -type d -exec echo "mkdir -p '{}/hooks' && ln -snf '$(which rh-multi-pre-commit)' '{}/hooks/pre-commit'" \; 2> /dev/null

# Run the command to make the change
find ~/ -name .git -type d -exec bash -c "mkdir -p '{}/hooks' && ln -snf '$(which rh-multi-pre-commit)' '{}/hooks/pre-commit'" \; 2> /dev/null
```

And you should be set up and ready to go! If want to check you can do a `ls -l
.git/hooks/pre-commit` in one of your existing projects and it should look
something like this:

```
.git/hooks/pre-commit -> /usr/local/bin/rh-multi-pre-commit
```

### Install Notes

You may be wondering why create a wrapper around pre-commit. Generally the
pre-commit framework prefers to work with `.pre-commit-config.yaml`s inside the
repo and if you're working with an open-source project that you expect others
outside of Red Hat to contribute to, enabling `rh-pre-commit` won't be an
option because they won't have access to rh-pre-commit or the patterns it uses.

rh-multi-pre-commit solves this by running pre-commit on the following
paths if they exist:

```
${HOME}/.config/pre-commit/config.yaml
.pre-commit-config.yaml
```

#### Resetting Config

```sh
rm -rf ~/.config/rh-gitleaks/
rm -rf ~/.cache/rh-gitleaks/
```

#### Advanced Options

The quickstart covers a basic install but in some cases folks might not
have sudo access on their system. In this case you can override the `PREFIX`
variable to have it install in a different location.

**IMPORTANT:** Make sure that the bin directory under the prefix that you
define is on your path before doing any of the other commands to enable it for
your repositories.

For example:

```sh
make install PREFIX="${HOME}/.local"
```

Now if that directory is on your path, the output of the `which` command should
look something like this:

```sh
$ which rh-pre-commit rh-gitleaks rh-multi-pre-commit
~/.local/bin/rh-pre-commit
~/.local/bin/rh-gitleaks
~/.local/bin/rh-multi-pre-commit
```

If you are moving an existing install to a local dir, you will need to
re-run the commands containing `ln -snf` above to update the links in
your projects.

### One-Off Installs (Not Recommended)

If you don't want to default to installing one of these hooks on all of your
projects. It is possible to do one-off installs. The danger here is that you
may forget to do it on new projects and that could result in something slipping
by.

```sh
# (Option 1) rh-pre-commit
cd /path/to/project
mkdir -p .git/hooks && ln -snf $(which rh-pre-commit) .git/hooks/pre-commit

# (Option 2) rh-multi-pre-commit
cd /path/to/project
mkdir -p .git/hooks && ln -snf $(which rh-multi-pre-commit) .git/hooks/pre-commit
# You will still need the pre-commit steps from the quickstart above.
```

## Ignoring False Leak Positives

This pre-commit hook will look for a `.gitleaks.toml` in the root of your
repo. You can add a global allow list that looks something like this:

```toml
[allowlist]
description = "Global Allowlist"

paths = [
  # Replace this with the regex for a path
  '''regex-for-file-path''',
]

regexes = [
  # Replace this with the regex for an existing match
  '''one-regex-within-the-already-matched-regex''',
]
```

And you can run the `rh-pre-commit` command from the root of your repo
to test to see if the changes work.

## Turning On/Off Checks

These options allow you to turn on/off different checks provided by this
package without having to remove the entire hook.

### Secrets Check (Default: On)

```sh
git config --bool hooks.checkSecrets false
```
