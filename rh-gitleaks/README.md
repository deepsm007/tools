# rh-gitleaks

This provides a wrapper around
[gitleaks 7.6.1](https://github.com/zricethezav/gitleaks/tree/v7.6.1)
to integrate it with our
[Pattern Server](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server).
Please read over the patterns server docs before setting this up.

## Contents

[[_TOC_]]

## Requirments

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
[this script](../scripts/uninstall-legacy-tools) to locate and remove them.

If you are unsure if you have the legacy versions of the script installed, you
can run the uninstall script to find out. It should only find and remove the
legacy scripts and will prompt you before doing so.

**NOTE**: This also removes any legacy versions of rh-pre-commit too. If those
are removed, you will need to install [the new version](../rh-pre-commit).

## Getting Started

**NOTE:** If you are using this tool as a part of
[rh-pre-commit](../rh-pre-commit), installing this tool is done automatically.

At the end of this (assuming the defaults are applied):

* `rh-gitleaks` and `rh-gitleaks-gh-account` will be installed.
* rh-gitleaks will be logged in and have a 2 year patterns server token


**Pull a fresh copy of the repo**

```sh
rm -rf /tmp/infosec-tools
git clone https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git /tmp/infosec-tools
# The rest of the commands assume you are in this subfolder of the repo
cd /tmp/infosec-tools/rh-gitleaks
```

**Install/Update the tools**

```sh
# If you need to install from a specific branch:
# git checkout <branch-name>

# This installs the tools but you will still need to configure them
make install
```

To have the tool walk you through the configuration:

```sh
rh-gitleaks configure
```

Please note the expiration date of the token in the output. You will need to
run `login` and update your token before the expiration date. As of writing
this a token lasts 2 years, so replacing your token on a yearly basis is a good
practice.

**NOTE:** If you are using a service account as described in the pattern
server's docs, you will enter in the API token provided from that process
instead of going to the server to get token.

## Notifications About Updates

Please follow/subscribe-to the
[Pattern Server](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server).
doc in The Source. There is a change log at the bottom that is updated when
there are new releases.

## Usage (rh-gitleaks)

All of the gitleaks args are expected to work except for `--config-path`
because that is managed by the wrapper.

This script pulls its own copy of gitleaks to ensure it matches the
versions supported by the patterns server.

`rh-gitleaks --help` will cover most of the options for the command.

Please be careful not to expose the patterns publicly!

### Options not listed under --help

To reset/refresh your Pattern Server API token, run
`rh-gitleaks login`.

To remove your Pattern Server API token, run `rh-gitleaks logout`.

To reset your configuration, run `rh-gitleaks configure`

To download the gitleaks binary before the first run, run `rh-gitleaks
pre-cache`.  This is useful to include as an install step when
installing rh-gitleaks in a container image so that it doesn't have to
download gitleaks each time a new container starts.

## Usage (rh-gitleaks-gh-account)

This is a wrapper around rh-gitleaks that runs it against all of the repos
under an account or org.

If the cli tool was not installed on your path, you can also call it via:
`python3 -m rh_gitleaks.gh_account`.

Once rh-gitleaks is setup, you can run `rh-gitleaks-gh-account --help` for
more info on how to use this tool.

Example:

```sh
# Scan all the repos under leaktk
rh-gitleaks-gh-account leaktk
```

**NOTE:** rh-gitleaks-gh-account exits when a 0 exit status even when leaks are
found. This is meant for finding leaks across an account/org rather than
setting up in a CI pipeline.

## Advanced Usage

The patterns server used by the tool can also be changed by setting the
`LEAKTK_PATTERN_SERVER_URL` env variable.

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
