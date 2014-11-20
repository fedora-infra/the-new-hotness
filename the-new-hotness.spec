%{!?_licensedir: %global license %%doc}

%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2:        %global __python2 /usr/bin/python2}
%{!?python2_sitelib:  %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global modname the-new-hotness

Name:               the-new-hotness
Version:            0.1.3
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

Requires:           python-bugzilla
Requires:           python-dogpile-cache
Requires:           fedmsg

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

%files
%doc README.rst
%license LICENSE
%{python2_sitelib}/hotness/
%{python2_sitelib}/the_new_hotness-%{version}*

%changelog
* Wed Nov 19 2014 Ralph Bean <rbean@redhat.com> - 0.1.3-1
- Latest upstream with some bugfixes.

* Mon Nov 17 2014 Ralph Bean <rbean@redhat.com> - 0.1.2-1
- Initial package for infrastructure.
