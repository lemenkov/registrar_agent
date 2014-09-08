Name:		registrar_agent
Version:	0.3
Release:	1%{?dist}
Summary:	A simple REGISTRAR redirector application
Group:		Applications/Internet
License:	GPLv2+
URL:		https://github.com/lemenkov/registrar_agent
BuildArch:      noarch
Source0:	https://github.com/lemenkov/registrar_agent/archive/%{version}/%{name}-%{version}.tar.gz
Requires:	python-sippy
Requires:	python-application
Requires(pre):  /usr/sbin/useradd
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service
Requires(postun): /sbin/service


%description
A simple REGISTRAR redirector application.


%prep
%setup -q


%build


%install
make install DESTDIR=$RPM_BUILD_ROOT
%if 0%{?el6}
install -p -m 0644 -D %{name}.upstart $RPM_BUILD_ROOT%{_sysconfdir}/init/%{name}.conf
%endif


%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || useradd -r -g %{name} -d / -s /sbin/nologin -c "SIP REGISTRAR redirector daemon" %{name}
exit 0


%post
#/sbin/chkconfig --add %{name}


%preun
if [ $1 = 0 ]; then
#        /sbin/service %{name} stop >/dev/null 2>&1
#        /sbin/chkconfig --del %{name}
fi


%postun
if [ "$1" -ge "1" ]; then
#        /sbin/service %{name} condrestart >/dev/null 2>&1
fi


%files
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/config.ini
%if 0%{?el7}%{?fedora}
# TODO add systemd
%else
%{_sysconfdir}/init/%{name}.conf
%endif
%{_sbindir}/%{name}
%attr(755,%{name},%{name}) %{_localstatedir}/run/%{name}

%changelog
