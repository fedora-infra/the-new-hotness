%{!?_licensedir: %global license %%doc}

%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2:        %global __python2 /usr/bin/python2}
%{!?python2_sitelib:  %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global modname the-new-hotness

Name:               the-new-hotness
Version:            0.7.3
Release:            1%{?dist}
Summary:            Consume anitya fedmsg messages to file bugzilla bugs

Group:              Development/Libraries
License:            LGPLv2+
URL:                http://pypi.python.org/pypi/the-new-hotness
Source0:            https://pypi.python.org/packages/source/t/%{modname}/%{modname}-%{version}.tar.gz
BuildArch:          noarch

BuildRequires:      python2-devel
BuildRequires:      python-setuptools

BuildRequires:      python-bugzilla
BuildRequires:      python-dogpile-cache
BuildRequires:      fedmsg
BuildRequires:      python-fedmsg-meta-fedora-infrastructure
BuildRequires:      python-six

Requires:           python-bugzilla
Requires:           python-dogpile-cache
Requires:           fedmsg
Requires:           python-fedmsg-meta-fedora-infrastructure
Requires:           python-six
Requires:           rebase-helper

%description
Fedmsg consumer that listens to release-monitoring.org and files bugzilla bugs
in response (to notify packagers that they can update their packages).

%prep
%setup -q -n %{modname}-%{version}

# Remove bundled egg-info in case it exists
rm -rf %{modname}.egg-info

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install -O1 --skip-build --root=%{buildroot}

# setuptools installs these, but we don't want them.
rm -rf %{buildroot}%{python2_sitelib}/tests/

%files
%doc README.rst
%license LICENSE
%{python2_sitelib}/hotness/
%{python2_sitelib}/the_new_hotness-%{version}*

%changelog
* Wed Apr 06 2016 Ralph Bean <rbean@redhat.com> - 0.7.3-1
- new version

* Tue Mar 08 2016 Ralph Bean <rbean@redhat.com> - 0.7.2-1
- new version

* Tue Mar 01 2016 Ralph Bean <rbean@redhat.com> - 0.7.1-1
- new version

* Mon Feb 29 2016 Ralph Bean <rbean@redhat.com> - 0.7.0-1
- new version

* Tue Nov 24 2015 Ralph Bean <rbean@redhat.com> - 0.6.4-1
- new version

* Fri Oct 09 2015 Ralph Bean <rbean@redhat.com> - 0.6.3-1
- new version

* Thu Oct 01 2015 Ralph Bean <rbean@redhat.com> - 0.6.2-1
- new version

* Fri Sep 25 2015 Ralph Bean <rbean@redhat.com> - 0.6.1-1
- new version

* Thu Sep 24 2015 Ralph Bean <rbean@redhat.com> - 0.6.0-1
- new version

* Fri Jun 05 2015 Ralph Bean <rbean@redhat.com> - 0.5.0-1
- new version

* Tue Apr 07 2015 Ralph Bean <rbean@redhat.com> - 0.4.1-1
- Small bump to the get the GitHub name right for anitya.

* Sat Mar 28 2015 Ralph Bean <rbean@redhat.com> - 0.4.0-1
- Map in anitya when monitoring flag is toggled.
- File bugs when newly mapped in anitya.
- Send patches to bugzilla.
- Comment on the bug when we failed to kick off a scratch build.
- Publish fedmsg messages about errors instead of emailing hapless admins.

* Tue Feb 24 2015 Ralph Bean <rbean@redhat.com> - 0.3.3-1
- Improved changelog format.
- Provide correct information when mapping new github backends.

* Sat Feb 21 2015 Ralph Bean <rbean@redhat.com> - 0.3.2-1
- Improved logging
- Only followup on rawhide builds.

* Tue Feb 17 2015 Ralph Bean <rbean@redhat.com> - 0.3.1-1
- Minor bugfix to rawhide build followup.

* Thu Jan 29 2015 Ralph Bean <rbean@redhat.com> - 0.3.0-1
- new version

* Mon Jan 12 2015 Ralph Bean <rbean@redhat.com> - 0.2.2-1
- Latest upstream.

* Thu Nov 20 2014 Ralph Bean <rbean@redhat.com> - 0.2.1-1
- Latest upstream with lots of bugfixes.
- New fedmsg messages included.

* Wed Nov 19 2014 Ralph Bean <rbean@redhat.com> - 0.1.3-1
- Latest upstream with some bugfixes.

* Mon Nov 17 2014 Ralph Bean <rbean@redhat.com> - 0.1.2-1
- Initial package for infrastructure.
