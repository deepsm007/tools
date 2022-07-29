# rh-pre-commit

A set of standard pre-commit hooks to run on your projects.

## Requires

* [rh-gitleaks](../rh-gitleaks) (which is handled during a `make install`)

## Ways To Install The Command

* Add dev-tools/rh-pre-commit/bin to your path
* Add dev-tools/bin to your path (This will install rh-gitleaks too)
* Run `sudo make install` to install them system wide (This will install rh-gitleaks too)

## Ways To Install As A Hook

These all assume you have `rh-pre-commit` somewhere on your path. If you need
help getting this set up, feel free send an email to infosec@redhat.com with
"InfoSec Dev Tools Support" in the subject.

It's also recommended to read through the git

### One-Off Install

```sh
cd /path/to/project
mkdir -p .git/hooks && ln -snf $(which rh-pre-commit) .git/hooks/pre-commit
```

#### Pros

* Easy to set up for a project

#### Cons

* This becomes the only pre-commit hook installed on your project
* This doesn't handle new projects


### Install For All New Projects

```sh
git config --global init.templateDir ~/.git-template
mkdir -p ~/.git-template/hooks && ln -snf $(which rh-pre-commit) ~/.git-template/hooks/pre-commit
```

#### Pros

* Handles setting it up for all new projects

#### Cons

* This becomes the only pre-commit hook installed on your new projects
* This doesn't handle exiting projects

### Use The pre-commit Tool

There is a pre-commit manager called [pre-commit](https://pre-commit.com/)
that makes managing multiple pre-commit hooks at once much easier.

Before installing it through pip, check to see if it's already available as a
package for your OS (e.g. `sudo dnf install pre-commit`).

There are some gotchas with this option though. Generally the pre-commit
framework prefers to work with `.pre-commit-config.yaml`s inside the project
and if you're working with an open-source project that you expect others out
side of Red Hat to contribute to, enabling `rh-pre-commit` won't be an option
because they won't have access to rh-pre-commit or the patterns it uses.

To still leverage the pre-commit framework to allow multiple checks you could
make a `pre-commit` script that looked something like this.

To make this a bit easier. There is a wrapper in this project called
`rh-mulit-pre-commit` that checks for configs in the following locations
in this order:

```
${HOME}/.config/pre-commit/config.yaml
.pre-commit-config.yaml
```

Here is an example config file that could be used with this tool:

```yaml
repos:
  - repo: local
    hooks:
      - id: rh-pre-commit
        name: Run standard RH pre-commit checks
        language: system
        entry: rh-pre-commit
```

You can then install the `rh-multi-pre-commit` tool using one of the methods
mentioned above for `rh-pre-commit` but just swapping out the name.

For this to work you'll need both `rh-multi-pre-commit` and `rh-pre-commit`
on your path.

#### One Off Install
cd /path/to/project
mkdir -p .git/hooks && ln -snf $(which rh-multi-pre-commit) .git/hooks/pre-commit

#### Install For All New Projects

```sh
git config --global init.templateDir ~/.git-template
mkdir -p ~/.git-template/hooks && ln -snf $(which rh-multi-pre-commit) ~/.git-template/hooks/pre-commit
```


