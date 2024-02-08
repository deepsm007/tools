Name: rh-gitleaks
Summary: scan git commits for leaks
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
BuildRequires: python3-requests
BuildRequires: pyproject-rpm-macros

Requires: leaktk-gitleaks7 python3-requests python3-jwt

%description
Frontend on gitleaks tool for scanning code commits

%prep
{{{ git_dir_setup_macro }}}

%build
%pyproject_wheel

%install
%pyproject_install

%check
%pytest

%files
%{_bindir}/rh-gitleaks
%{_bindir}/rh-gitleaks-gh-account
%{_bindir}/rh-gitleaks-gl-account
%{python3_sitelib}/rh_gitleaks-*.dist-info/
%{python3_sitelib}/rh_gitleaks/

%changelog
* Thu Feb 8 2024 Braxton Plaxco <bplaxco@redhat.com> - 2.2.0-1
- Require leaktk-gitleaks7 package
- Updated the github.com/leaktk/bin binary location and hashes
- Updated the user agent string

* Wed Nov 15 2023 Daniel P. Berrangé <berrange@redhat.com> - 2.1.0-1
- Initial package + misc tweaks by bplaxco & jpadman
