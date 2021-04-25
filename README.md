# InfoSec Developer Tools

Tools to aid development across InfoSec. Here, a tool is defined as something
that can be run on a dev's laptop rather than as a service on a remote server.
It is also possible that CI/CD processes may also consume the tools for
automation.

## Contents

[[_TOC_]]

## Using The Tools

### Make Install

```
cd ../{{tooldir}}/

# Read the README

make install
{{tool}} --help
```

### Add `./bin` to Your Path

If you source the bin folder in this project. Most tools should be available
to you. There might be some that can't be added this way. If you see a tool
missing, please check the project's README or file an issue on the project.

### Install RPM

Coming soon!

## Contributing

Don't see what you're looking for, is something broken, have an idea?
See the [CONTRIBUTING.md](./CONTRIBUTING.md) file for information on how to
report problems and help out.
