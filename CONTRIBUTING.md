# Contributing

This guide only covers this project in the InfoSec Developer Workbench. If you
wish to contribute to another project, please review that project's
contribution guide.

## What project is looking for

### Vision

Capture the scripts/tools used for automation and development in this repo to
enable developers to run the same scripts the CI server's are running on their
local laptops.

Generally things in this repo should give people more options and pave a road
for easier development, but not force them down a certian path.

### Types of contributions

* New Tools!
* Bug Fixes!
* Tool Improvements!

We also probably need a `cli-tool` (or similar) building-block for creating
new tools.

## How to...

### Contribute

* Read this and the README completely
* Pull the repo and create a feature branch for your changes[1]
* Submit a merge request (someone should be notified)

[1] Fork the repo if you don't have access to create a branch.

#### Tool Format

Each tool should:

* Have it's own folder
* Support the `--help` flag
* Have a Makefile that implements the [standard Makefile](https://gitlab.corp.redhat.com/infosec-public/developer-workbench/guides/-/blob/main/README.md#interacting-with-projects-through-make)
* Support `make install` for local installs
* Support `make rpm` to package it as an RPM
* Have a script in thi project's `./bin` folder to run it without installing it.

### Get in touch

If you have any questions, submit an issue on the repo and that'll notify
someone.
