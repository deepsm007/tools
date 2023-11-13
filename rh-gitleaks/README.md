# rh-gitleaks

This provides a wrapper around
[gitleaks 7.6.1](https://github.com/zricethezav/gitleaks/tree/v7.6.1)
to integrate it with our
[Pattern Server](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server).
Please read over the patterns server docs before setting this up.

## Contents

[[_TOC_]]

## Requirements

You will need the following installed on your system:

* `python3`
* `pip`
* `make`

## Supported Operating Systems

* Linux (x86\_64)
* Linux (arm64)
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

* `rh-gitleaks`, `rh-gitleaks-gh-account` and `rh-gitleaks-gl-account`
  will be installed.
* rh-gitleaks will be logged in and have a 2-year patterns server token


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

Please follow the
[LeakTK Changelog blog](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_changelog/)
for all important updates.

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

This is a wrapper around rh-gitleaks that runs it against all of the
github.com repos under an account or org.

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

## Usage (rh-gitleaks-gl-account)

This is a wrapper around rh-gitleaks that runs it against all of the gitlab
repos under an account or org.

If the cli tool was not installed on your path, you can also call it via:
`python3 -m rh_gitleaks.gl_account`.

Once rh-gitleaks is setup, you can run `rh-gitleaks-gl-account --help` for
more info on how to use this tool.

Example, with default gitlab.com server:

```sh
# Scan all the repos under the libvirt group on gitlab.com:
rh-gitleaks-gl-account libvirt
```

Example, with an alternative server:

```sh
# Scan all the repos under an account on GNOME gitlab
rh-gitleaks-gl-account gitlab.gnome.org/dberrange
```

**NOTE:** rh-gitleaks-gl-account exits when a 0 exit status even when leaks are
found. This is meant for finding leaks across an account/org rather than
setting up in a CI pipeline.

## Pattern Server Auth Token

The pattern server uses a JWT to authenticate access to the patterns and to
determine access to the patterns provided. This is usually set during the
`rh-gitleaks configure` step or by running `rh-gitleaks login`. But for
automation use cases, it can be set set non-interactively as well:

The auth token can be set using the `LEAKTK_PATTERN_SERVER_AUTH_TOKEN`
environment variable. If this is set it takes precedence over other tokens.

Alternatively, the token can be placed at `$XDG_CONFIG_HOME/rh-gitleaks/auth.jwt`.
(The value of `$XDG_CONFIG_HOME` will default to `$HOME/.config` if it isn't
set). This is also where `rh-gitleaks login` writes the token.

## Advanced Usage

### Using a different pattern server

The patterns server used by the tool can also be changed by setting the
`LEAKTK_PATTERN_SERVER_URL` env variable.

### Using a different gitleaks executable

Rh-gitleaks pulls a pre-built binary from the leaktk GitHub project. The
project and the binaries are maintained by members of the InfoSec team. We use
a specific version of gitleaks rather than pulling a system package to ensure
that deep integrations across our whole tool chain stay compatible. There
were was a regression with gitleaks v8 when it first came out, which stalled
our upgrade, but that has now been fixed and we are working towards that now.

If for some reason you desire to use a different executable than the
one pulled by the tool. All you have to do is:

1. Make sure it is compatible with the version used by the tool
2. Run this command to figure out where to place the executable:

   ```
   python3 -c 'import platform; print(f"~/.cache/rh-gitleaks/gitleaks-7.6.1-{platform.system().lower()}-{platform.machine()}")'
   ```
3. Place your custom executable at that location.

For example for me it is at:

```
~/.cache/rh-gitleaks/gitleaks-7.6.1-linux-x86_64
```

## Troubleshooting

This section covers some basic troubleshooting steps. If you still need help,
please email infosec@redhat.com for assistance and provide a link to this
README for context.

### Command Not Found

If you get a `command not found` error and you know the scripts were installed,
it's likely that the place the scripts were installed is not on your path.

When you run `make install`, you may see a warning like this towards the end:

```
WARNING: The scripts rh-gitleaks, rh-gitleaks-gh-account and rh-gitleaks-gl-account are installed in '/home/user/.local/bin' which is not on PATH.
Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.`
```

If you add the directory from the warning you saw to your PATH (this will be
different than the one in the example above), that should resolve the problem.
If you're not sure what it means to "add a directory to your path", a quick
search online should provide some examples to help you get set up.

Alternatively, you can reference the commands through their modules directly:

* `rh-gitleaks` becomes `python3 -m rh_gitleaks`
* `rh-gitleaks-gh-account` becomes `python3 -m rh_gitleaks.gh_account`
* `rh-gitleaks-gl-account` becomes `python3 -m rh_gitleaks.gl_account`
