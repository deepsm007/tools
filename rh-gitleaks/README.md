# rh-gitleaks

These tools provide wrappers around [gitleaks](https://github.com/zricethezav/gitleaks)
to make it easier to use within Red Hat.

## Contents

[[_TOC_]]

## Ways To Install

* Add dev-tools/rh-gitleaks/bin to your path
* Add dev-tools/bin to your path
* Run `sudo make install` to install them system wide

## Tools

### rh-gitleaks

This wrapper integrates the gitleaks command with our
[patterns server](https://source.redhat.com/departments/it/it-information-security/wiki/pattern_distribution_server)
which is accessible outside of Red Hat's network. Please read the patterns
server user guide before setting this up.

The version of gitleaks used is listed towards the top of the script and
all of the gitleaks args are expected to work except for `--config-path`
because that is managed by the wrapper.

Run `rh-gitleaks --help` for initial setup instructions. Then once you are
set up you can run it again to see the command line options for gitleaks.

Supported Operating Systems:

* Linux (amd64)
* (Looking to collaborate with someone for Mac support)

This script pulls its own copy of gitleaks to ensure it matches the
versions supported by the patterns server.

The patterns server used by the tool can also be updated by setting the
`RH_GITLEAKS_PATTERNS_SERVER` env variable.

Please be careful not to expose these patterns publicly.

### rh-gitleaks-gh-account

This is wraps `rh-gitleaks` and can be useful for scanning an entire
GitHub account or organization.

Example Usage: `rh-gitleaks-gh-account bplaxco`.

This wrapper does not support passing arguments to `rh-gitleaks` and the
`rh-gitleaks` command must be on your path for this to work.
