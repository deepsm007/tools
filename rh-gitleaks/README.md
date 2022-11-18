# rh-gitleaks

This provides a wrapper around
[gitleaks 7.6.1](https://github.com/zricethezav/gitleaks/tree/v7.6.1)
to integrate it with our
[Pattern Distribution Server](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server).
Please read over the patterns server docs before setting this up.

## Contents

[[_TOC_]]

## Supported Operating Systems

* Linux (x86\_64)
* Mac (x86\_64)

Arm64 support for Mac is planned.

## Setup and Upgrades

This section assumes you already have Python 3 and pip installed on your system.

**NOTE:** If you are using this tool as a part of `rh-pre-commit`,
setup and upgrades are already covered in `rh-pre-commit`'s docs.

To install/upgrade from the **default branch**:

```sh
python3 -m pip install --upgrade "git+https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git#subdirectory=rh-gitleaks"
```

To install from a **specific branch**:
```sh
BRANCH="replace-me-with-the-desired-branch"
python3 -m pip install --upgrade "git+https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools.git@${BRANCH}#subdirectory=rh-gitleaks"
```

This should place `rh-gitleaks` on your path. If not, replace `rh-gitleaks`
with `python3 -m rh_gitleaks` when running the commands below. You are also
welcome to submit an issue on this repo if you are having trouble with the
install process.

To use the tool you'll need to configure API credentials so it can access the
patterns provided by the Pattern Distribution Server.

To have the tool walk you through the configuration:

```sh
rh-gitleaks configure
```

Please note the expiration date of the token in the output. You will need
to run `login` and update your token before the expiration date.
As of writing this a token lasts 2 years, so replacing your token on a yearly
basis is a good practice.

**NOTE:** If you are using a service account, as described in the pattern
distribution server's docs, you will enter in the API token provided from that
process instead of going to the server to get token.

## Usage

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

## Notifications About Updates

Please follow/subscribe-to the
[Pattern Distribution Server](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server).
doc in The Source. There is a change log at the bottom that is updated when
there are new releases of the tool.

## Advanced Usage

The patterns server used by the tool can also be changed by setting the
`RH_GITLEAKS_PATTERNS_SERVER` env variable.
