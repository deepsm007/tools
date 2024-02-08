Name: rh-pre-commit
Summary: Wrapper around pre-commit for global configuration
Version: 2.2.0
Release: 1
License: MIT
Url: https://gitlab.corp.redhat.com/infosec-public/developer-workbench/tools
Source: {{{ git_dir_pack }}}

BuildArch: noarch

BuildRequires: python3
BuildRequires: python3-devel
BuildRequires: python3-hatchling
BuildRequires: python3-jwt
BuildRequires: python3-pip
BuildRequires: python3-pytest
BuildRequires: python3-pyyaml
BuildRequires: python3-requests
BuildRequires: pyproject-rpm-macros
BuildRequires: git
BuildRequires: pre-commit
BuildRequires: rh-gitleaks


Requires: git rh-gitleaks pre-commit python3-pyyaml

%description
Wrapper for pre-commit to support global configuration and Red Hat Internal
Tooling

%prep
{{{ git_dir_setup_macro }}}

%build
%pyproject_wheel

%install
%pyproject_install

%check
%pytest

%files
%{_bindir}/rh-pre-commit
%{_bindir}/rh-multi-pre-commit
%{python3_sitelib}/rh_pre_commit-*.dist-info/
%{python3_sitelib}/rh_pre_commit/

%changelog
* Thu Feb 8 2024 Braxton Plaxco <bplaxco@redhat.com> - 2.2.0-1
- Change how unknown version is displayed for consistency
- Resolved "Rh-pre-commit.commit-msg fails with worktrees" issue 17

* Mon Nov 27 2023 Joshua Padman <jpadman@redhat.com> - 2.1.0-1
- Initial package for rpkg & copr
