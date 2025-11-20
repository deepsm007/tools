# Release

This doc covers how to do a release of the tools here.

NOTE: when doing a release make sure that rh-pre-commit always has it's own
latest commit that is tagged with it's current version. This keeps
`pre-commit autoupdate` from fetching a weird tag.

You should be able to test it via:

```sh
git tag --points-at "$(git describe FETCH_HEAD --tag --abbrev=0)"
```

## Steps

1. Make sure the versions are updated
1. Run `make specfile` and commit the changes
1. Draft the [changelog entry](https://source.redhat.com/departments/it/it-information-security/leaktk/leaktk_changelog)
1. Review and test code
   1. Make sure there are no issues
   1. Make sure docs are taken into account
   1. Make sure GitLab issues have been addressed
1. Merge into main
1. Checkout main and pull latest
1. Run the following replacing the version
   1. git commit --allow-empty -m "rh-gitleaks-VERSION"
   1. git tag rh-gitleaks-VERSION
   1. git commit --allow-empty -m "rh-pre-commit-VERSION"
   1. git tag rh-pre-commit-VERSION
   1. git push && git push --tags
1. Build [RPMs in COPR](https://copr.devel.redhat.com/coprs/g/infosec-public/leaktk/)
1. Do a quickstart.sh install again to do one last round of testing and verify versions
1. Publish the changelog
1. Update the .pre-commit-config.yaml through a pre-commit autoupdate and merge in the changes
1. Close out any now-resolved GitLab issues
