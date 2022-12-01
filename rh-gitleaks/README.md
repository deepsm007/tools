# rh-gitleaks

This provides a wrapper around
[gitleaks 7.6.1](https://github.com/zricethezav/gitleaks/tree/v7.6.1)
to integrate it with our
[Pattern Distribution Server](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server).
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

Arm64 support for Mac is planned.

For additional OS support reach out to infosec@redhat.com.

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
# NOTE: If you need to install from a specific branch
# run a "git checkout <branch-name>" here

# This installs the tools but you will still need to configure them
make install
```

To have the tool walk you through the configuration:

```sh
rh-gitleaks configure
```

Please note the expiration date of the token in the output. You will need
to run `login` and update your token before the expiration date.
As of writing this a token lasts 2 years, so replacing your token on a yearly
basis is a good practice.

**NOTE:** If you are using a service account as described in the pattern
distribution server's docs, you will enter in the API token provided from that
process instead of going to the server to get token.

## Notifications About Updates

Please follow/subscribe-to the
[Pattern Distribution Server](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server).
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

To reset/refresh your Pattern Distribution Server API token, run
`rh-gitleaks login`.

To remove your Pattern Distribution Server API token, run `rh-gitleaks logout`.

To reset your configuration, run `rh-gitleaks configure`

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
`RH_GITLEAKS_PATTERNS_SERVER` env variable.

## Troubleshooting

This section covers some basic troubleshooting steps. If you still need help,
please email infosec@redhat.com for assistance and provide a link to this
README for context.

### Command not found

If you run the command and get a `command not found` error, you can
reference the commands through their modules directly.

* `rh-gitleaks` becomes `python3 -m rh_gitleaks`
* `rh-gitleaks-gh-account` becomes `python3 -m rh_gitleaks.gh_account`
