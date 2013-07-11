Name:           fedora-gooey-karma
Version:        0.1
Release:        1%{?dist}
Summary:        GUI tool for adding karma to Bodhi system. Similar to fedora-easy-karma.

Group:          Development/Tools
License:        GPLv2+
URL:            https://fedoraproject.org/wiki/Fedora_Gooey_Karma

Source0:        fedora-gooey-karma.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

Requires:       python-fedora
Requires:       fedora-cert
Requires:       yum
Requires:       yum-utils
Requires:       bodhi-client
Requires:       python-pyside

%description
Fedora-gooey-karma helps you to easily and fast provide feedback for all testing
updates that you have currently installed and browse the available ones. It is 
similar tool to fedora-easy-karma but with graphical front-end.


%prep
%setup -q -n fedora-gooey-karma


%build


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT prefix=%{_prefix}


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{_bindir}/fedora-gooey-karma
/usr/share/fedora-gooey-karma


%changelog
* Thu Jul 10 2013 Branislav Blaskovic <branislav@blaskovic.sk> - 0.1-1
- Initial spec file
