# rh-pre-commit

A set of standard pre-commit hooks to run on your projects.

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

## Requires

* [rh-gitleaks](../rh-gitleaks) (which is handled during a `make install`)

## Updates

Please subscribe to the [patterns server user guide](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server)
for information about updates and changes.

## Ways To Install The Command

* Add dev-tools/rh-pre-commit/bin to your path
* Add dev-tools/bin to your path (This will install rh-gitleaks too)
* Run `sudo make install` to install them system wide (This will install rh-gitleaks too)

Then you'll want to run `rh-pre-commit`[1] and follow the steps outlined for
getting set up with a API token for accessing leak patterns.

[1] This will kick off a scan once everything is set up so it would be good to
run it from a small folder like an existing project rather than from your home
folder.

## Ways To Install As A Hook

Thes options assume you have `rh-pre-commit` somewhere on your path. If you
need help getting this set up, feel free send an email to infosec@redhat.com
with "InfoSec Dev Tools Support" in the subject.

It's also recommended to read through the git's documentation on hooks if you
want a deeper understanding of how these work.

### One-Off Install (Not Optimal)

```sh
cd /path/to/project
mkdir -p .git/hooks && ln -snf $(which rh-pre-commit) .git/hooks/pre-commit
```

#### Pros

* Easy to set up for a project

#### Cons

* This becomes the only pre-commit hook installed on your project
* This doesn't handle new projects


### Install For All New Projects (Good If you Only Want These Hooks)

```sh
git config --global init.templateDir ~/.git-template
mkdir -p ~/.git-template/hooks && ln -snf $(which rh-pre-commit) ~/.git-template/hooks/pre-commit
```

#### Pros

* Handles setting it up for all new projects

#### Cons

* This becomes the only pre-commit hook installed on your new projects
* This doesn't handle exiting projects[1]

[1] But you could always run something like this to get it set up on
all of your existing projects:

```sh
# replace workspace with the path to where you store your projects
find workspace -name .git -type d -exec bash -c "mkdir -p {}/hooks && ln -snf $(which rh-pre-commit) {}/hooks/pre-commit" \;
```

### Use rh-multi-pre-commit (Recommended)

There is a pre-commit manager called [pre-commit](https://pre-commit.com/)
that makes managing multiple pre-commit hooks at once much easier. The
`rh-multi-pre-commit` script leverages that to allow you to place the config
outside of the project while still using `.pre-commit-config.yaml`s defined
in the project. Before installing pre-commit through pip, check to see if it's
already available as a package for your OS (e.g. `sudo dnf install
pre-commit`).

You may be wondering why use this instead of pre-commit directly. There are
some gotchas with using it the way it's meant to be used by default. Generally
the pre-commit framework prefers to work with `.pre-commit-config.yaml`s inside
the repo and if you're working with an open-source project that you expect
others out side of Red Hat to contribute to, enabling `rh-pre-commit` won't be
an option because they won't have access to rh-pre-commit or the patterns it
uses.

rh-multi-pre-commit solves this by runing pre-commit on the following
paths if they exist:

```
${HOME}/.config/pre-commit/config.yaml
.pre-commit-config.yaml
```

Here is an example `${HOME}/.config/pre-commit/config.yaml` file that could be
used with this tool:

```yaml
repos:
  - repo: local
    hooks:
      - id: rh-pre-commit
        name: Run standard RH pre-commit checks
        language: system
        entry: rh-pre-commit
```

#### One Off Install

```sh
cd /path/to/project
mkdir -p .git/hooks && ln -snf $(which rh-multi-pre-commit) .git/hooks/pre-commit
```

#### Install For All New Projects

```sh
git config --global init.templateDir ~/.git-template
mkdir -p ~/.git-template/hooks && ln -snf $(which rh-multi-pre-commit) ~/.git-template/hooks/pre-commit
```

#### Pros

* You can manage multiple pre-commit hooks in and outside of projects

#### Cons

* You have to run the one-off installs inside existing projects[1]

[1] But you could always run something like this to get it set up on
all of your projects:

```sh
# replace workspace with the path to where you store your projects
find workspace -name .git -type d -exec bash -c "mkdir -p {}/hooks && ln -snf $(which rh-multi-pre-commit) {}/hooks/pre-commit" \;
```
