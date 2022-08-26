# rh-pre-commit

A set of standard [pre-commit hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) to run on your projects.

## Contents

[[_TOC_]]

## Supported Operating Systems

* Linux (amd64)
* Mac (amd64)

For additional OS support reach out to infosec@redhat.com

## Updates

Please subscribe to the [patterns server user guide](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server)
for information about changes.

The installing and updating section below covers how to update the CLI tool if
there's been a change.

## Installing and Updating

The quickstart below covers how to do a full initial install and set up access
to the patterns server.

**Go to the folder where you want to clone this repo**

```sh
cd ~/
```

**Clone the repo** (if the repo is already cloned, do a `git pull` from inside the repo instead)

```sh
git clone https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git infosec-dev-tools
```

**Go to the `rh-pre-commit` folder**

```
cd ./infosec-dev-tools/rh-pre-commit/
```

**Install the hooks** (if doing an update, stop after this step)

If you don't have sudo access on your system, see "Local Install" below.

```sh
sudo make install
```

**Install pre-commit** 

For Fedora

```sh
sudo dnf install -y pre-commit
```

For Macs with brew

```
brew install pre-commit
```

For Other Operating Systems

```
pip install pre-commit # and make sure it's on your path when you're done
```

**Configure rh-multi-pre-commit**

```sh
mkdir -p ~/.config/pre-commit/
cp ./etc/pre-commit/config.yaml ~/.config/pre-commit/config.yaml
```

**Make the hooks the default for all new repos** (cloned or created).

```sh
git config --global init.templateDir ~/.git-template
mkdir -p ~/.git-template/hooks && ln -snf $(which rh-multi-pre-commit) ~/.git-template/hooks/pre-commit
```

**Configure the patterns server**

```sh
mkdir -p ~/.config/rh-gitleaks
```

* Go to https://patterns.security.redhat.com/token
* Copy the token and put it at ~/.config/rh-gitleaks/auth.jwt

**Confirm you see the help options and no errors**

```sh
rh-gitleaks --help
```

**Set up the hook for existing projects**

If you don't want to enable it for all repos see the "Enabling for Ad-Hoc Repos" section.

```sh
# You can run this first command to see what WOULD be updated before actually making the change. 
# If you don't like the repos it touches, you can change the starting-point (i.e. ~/) to 
# be the path to where you store your repos and run it again and review the output.
# 
# After you are happy with the output, run the comamnd containing "bash -c" below
# with the starting-point you want to use to enable the pre-commit hook for all 
# of the repos under that folder.
find ~/ -name .git -type d -exec echo "mkdir -p '{}/hooks' && ln -snf '$(which rh-multi-pre-commit)' '{}/hooks/pre-commit'" \; 2> /dev/null

# Run the command to make the change
find ~/ -name .git -type d -exec bash -c "mkdir -p '{}/hooks' && ln -snf '$(which rh-multi-pre-commit)' '{}/hooks/pre-commit'" \; 2> /dev/null
```

**Confirming the setup**

And you should be set up and ready to go! If want to check you can do a `ls -l
.git/hooks/pre-commit` in one of your existing projects and it should look
something like this:

```
.git/hooks/pre-commit -> /usr/local/bin/rh-multi-pre-commit
```

You could also create a new local repo with a file containing
```
secret="8P+eZAqUb4q24DsPf30A3NqkHGw7ZkItbp77z8X8zmxS+IDO9hQH9mh68h309LLou4rz1ZtyNg/0S81YWtuPUA=="
```
in it and try to commit it. If things are set up properly you should get a message
saying that you have a leak and if it's a fals positive you will need to add a 
`.gitleaks.toml` to your repo.

**And Your Done!**

### Resetting Config

```sh
rm -rf ~/.config/rh-gitleaks/
rm -rf ~/.cache/rh-gitleaks/
```

### Local Install

The quickstart covers a basic install but in some cases folks might not
have sudo access on their system. In this case you can override the `PREFIX`
variable to have it install in a different location. It will install it
under `${PREFIX}/bin`

**IMPORTANT:** If you do this, you'll want to make sure that the bin folder is on your
path before running the commands to enable it for your repos. Otherwise `which rh-multi-pre-commit`
won't return the path to the script.

For example:

```sh
make install PREFIX="${HOME}/.local"

# In this case you will want to make sure to have PATH="${HOME}/.local/bin:${PATH}" in your .bashrc or .zshrc
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

### Enabling for Ad-Hoc Repos

If you don't want to default to enabling one of these hooks on all of your
projects. It is possible to do one-off enables. The danger here is that you
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

### Reason for rh-multi-pre-commit

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

To turn off checks in a repo
```sh
git config --bool hooks.checkSecrets false
```

To turn on checks in a repo
```sh
git config --bool hooks.checkSecrets true
```
