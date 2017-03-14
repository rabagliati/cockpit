#
# This file is maintained at the following location:
# https://github.com/cockpit-project/cockpit/blob/master/tools/cockpit.spec
#
# If you are editing this file in another location, changes will likely
# be clobbered the next time an automated release is done.
#
# Check first cockpit-devel@lists.fedorahosted.org
#
# Globals that may be defined elsewhere
#  * Version 122
#  * wip 1
#

# earliest base that the subpackages work on; the instances of this get computed/updated
# by tools/gen-spec-dependencies during "make dist", but keep a hardcoded fallback
%define required_base 122

%if 0%{?centos}
%define rhel 0
%endif

%define _hardened_build 1

# define to build the dashboard
%define build_dashboard 1

%define libssh_version 0.7.1
%if 0%{?fedora} > 0 && 0%{?fedora} < 22
%define libssh_version 0.6.0
%endif

Name:           cockpit
Summary:        A user interface for Linux servers

License:        LGPLv2+
URL:            http://cockpit-project.org/

Version:        0
%if %{defined wip}
Release:        1.%{wip}%{?dist}
Source0:        cockpit-%{version}.tar.gz
%else
Release:        1%{?dist}
Source0:        https://github.com/cockpit-project/cockpit/releases/download/%{version}/cockpit-%{version}.tar.xz
%endif

BuildRequires: pkgconfig(gio-unix-2.0)
BuildRequires: pkgconfig(json-glib-1.0)
BuildRequires: pam-devel

BuildRequires: autoconf automake
BuildRequires: /usr/bin/python
BuildRequires: intltool
%if %{defined build_dashboard}
BuildRequires: libssh-devel >= %{libssh_version}
%endif
BuildRequires: openssl-devel
BuildRequires: zlib-devel
BuildRequires: krb5-devel
BuildRequires: libxslt-devel
BuildRequires: docbook-style-xsl
BuildRequires: glib-networking
BuildRequires: sed
BuildRequires: git

BuildRequires: glib2-devel >= 2.37.4
BuildRequires: systemd-devel
BuildRequires: pcp-libs-devel
BuildRequires: krb5-server
BuildRequires: gdb

# For documentation
BuildRequires: xmlto

# This is the "cockpit" metapackage. It should only
# Require, Suggest or Recommend other cockpit-xxx subpackages

Requires: %{name}-bridge = %{version}-%{release}
Requires: %{name}-ws = %{version}-%{release}
%if %{defined build_dashboard}
Requires: %{name}-dashboard = %{version}-%{release}
%endif
Requires: %{name}-system = %{version}-%{release}

# Optional components (for f24 we use soft deps)
%if 0%{?fedora} >= 24 || 0%{?rhel} >= 8
Recommends: %{name}-networkmanager = %{version}-%{release}
Recommends: %{name}-storaged = %{version}-%{release}
%ifarch x86_64 %{arm} aarch64 ppc64le
Recommends: %{name}-docker = %{version}-%{release}
%endif
Suggests: %{name}-pcp = %{version}-%{release}
Suggests: %{name}-kubernetes = %{version}-%{release}
Suggests: %{name}-selinux = %{version}-%{release}

# Older releases need to have strict requirements
%else
Requires: %{name}-networkmanager = %{version}-%{release}
Requires: %{name}-storaged = %{version}-%{release}
%ifarch x86_64 armv7hl
Requires: %{name}-docker = %{version}-%{release}
%endif

%endif

%description
Cockpit runs in a browser and can manage your network of GNU/Linux
machines.

%files
%{_docdir}/%{name}/AUTHORS
%{_docdir}/%{name}/COPYING
%{_docdir}/%{name}/README.md
%dir %{_datadir}/%{name}
%{_datadir}/appdata/cockpit.appdata.xml
%{_datadir}/applications/cockpit.desktop
%{_datadir}/pixmaps/cockpit.png
%doc %{_mandir}/man1/cockpit.1.gz

%prep
%setup -q

# Apply patches using git in order to support binary patches. Note that
# we also reset mtimes since patches should be "complete" and include both
# generated and source file changes
# Keep this in sync with tools/debian/rules.
if [ -n "%{patches}" ]; then
	git init
	git config user.email "unused@example.com" && git config user.name "Unused"
	git config core.autocrlf false && git config core.safecrlf false && git config gc.auto 0
	git add -f . && git commit -a -q -m "Base" && git tag -a initial --message="initial"
	git am --whitespace=nowarn %{patches}
	touch -r $(git diff --name-only initial..HEAD) .git
	rm -rf .git
fi

%build
exec 2>&1
%configure --disable-silent-rules --with-cockpit-user=cockpit-ws --with-branding=auto --with-selinux-config-type=etc_t %{?rhel:--without-storaged-iscsi-sessions} %{!?build_dashboard:--disable-ssh}
make -j4 %{?extra_flags} all

%check
exec 2>&1
make -j4 check

%install
make install DESTDIR=%{buildroot}
make install-tests DESTDIR=%{buildroot}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/pam.d
install -p -m 644 tools/cockpit.pam $RPM_BUILD_ROOT%{_sysconfdir}/pam.d/cockpit
rm -f %{buildroot}/%{_libdir}/cockpit/*.so
install -p -m 644 AUTHORS COPYING README.md %{buildroot}%{_docdir}/%{name}/

# On RHEL we don't yet show options for changing language
%if 0%{?rhel}
echo '{ "linguas": null, "machine-limit": 5 }' > %{buildroot}%{_datadir}/%{name}/shell/override.json
%endif

# Build the package lists for resource packages
echo '%dir %{_datadir}/%{name}/base1' > base.list
find %{buildroot}%{_datadir}/%{name}/base1 -type f >> base.list
echo '%{_sysconfdir}/cockpit/machines.d' >> base.list

%if %{defined build_dashboard}
echo '%dir %{_datadir}/%{name}/dashboard' >> dashboard.list
find %{buildroot}%{_datadir}/%{name}/dashboard -type f >> dashboard.list
find %{buildroot}%{_datadir}/%{name}/ssh -type f >> dashboard.list
%else
rm -rf %{buildroot}/%{_datadir}/%{name}/dashboard
rm -rf %{buildroot}/%{_datadir}/%{name}/ssh
touch dashboard.list
%endif

echo '%dir %{_datadir}/%{name}/pcp' >> pcp.list
find %{buildroot}%{_datadir}/%{name}/pcp -type f >> pcp.list

echo '%dir %{_datadir}/%{name}/realmd' >> system.list
find %{buildroot}%{_datadir}/%{name}/realmd -type f >> system.list

echo '%dir %{_datadir}/%{name}/tuned' >> system.list
find %{buildroot}%{_datadir}/%{name}/tuned -type f >> system.list

echo '%dir %{_datadir}/%{name}/shell' >> system.list
find %{buildroot}%{_datadir}/%{name}/shell -type f >> system.list

echo '%dir %{_datadir}/%{name}/systemd' >> system.list
find %{buildroot}%{_datadir}/%{name}/systemd -type f >> system.list

echo '%dir %{_datadir}/%{name}/users' >> system.list
find %{buildroot}%{_datadir}/%{name}/users -type f >> system.list

echo '%dir %{_datadir}/%{name}/kdump' >> kdump.list
find %{buildroot}%{_datadir}/%{name}/kdump -type f >> kdump.list

echo '%dir %{_datadir}/%{name}/sosreport' > sosreport.list
find %{buildroot}%{_datadir}/%{name}/sosreport -type f >> sosreport.list

echo '%dir %{_datadir}/%{name}/subscriptions' > subscriptions.list
find %{buildroot}%{_datadir}/%{name}/subscriptions -type f >> subscriptions.list

echo '%dir %{_datadir}/%{name}/storaged' > storaged.list
find %{buildroot}%{_datadir}/%{name}/storaged -type f >> storaged.list

echo '%dir %{_datadir}/%{name}/networkmanager' > networkmanager.list
find %{buildroot}%{_datadir}/%{name}/networkmanager -type f >> networkmanager.list

echo '%dir %{_datadir}/%{name}/ostree' > ostree.list
find %{buildroot}%{_datadir}/%{name}/ostree -type f >> ostree.list

echo '%dir %{_datadir}/%{name}/machines' > machines.list
find %{buildroot}%{_datadir}/%{name}/machines -type f >> machines.list

# on CentOS systems we don't have the required setroubleshoot-server packages
%if 0%{?centos}
rm -rf %{buildroot}%{_datadir}/%{name}/selinux
%else
echo '%dir %{_datadir}/%{name}/selinux' > selinux.list
find %{buildroot}%{_datadir}/%{name}/selinux -type f >> selinux.list
%endif

%ifarch x86_64 %{arm} aarch64 ppc64le
echo '%dir %{_datadir}/%{name}/docker' > docker.list
find %{buildroot}%{_datadir}/%{name}/docker -type f >> docker.list
%else
rm -rf %{buildroot}/%{_datadir}/%{name}/docker
touch docker.list
%endif

%ifarch x86_64 ppc64le
%if %{defined wip}
%else
rm %{buildroot}/%{_datadir}/%{name}/kubernetes/override.json
%endif
echo '%dir %{_datadir}/%{name}/kubernetes' > kubernetes.list
find %{buildroot}%{_datadir}/%{name}/kubernetes -type f >> kubernetes.list
%else
rm -rf %{buildroot}/%{_datadir}/%{name}/kubernetes
touch kubernetes.list
%endif

sed -i "s|%{buildroot}||" *.list

# Build the package lists for debug package, and move debug files to installed locations
find %{buildroot}/usr/src/debug%{_datadir}/%{name} -type f -o -type l > debug.partial
sed -i "s|%{buildroot}/usr/src/debug||" debug.partial
sed -n 's/\.map\(\.gz\)\?$/\0/p' *.list >> debug.partial
sed -i '/\.map\(\.gz\)\?$/d' *.list
tar -C %{buildroot}/usr/src/debug -cf - . | tar -C %{buildroot} -xf -
rm -rf %{buildroot}/usr/src/debug

# On RHEL kdump, subscriptions, networkmanager, selinux, and sosreport are part of the system package
%if 0%{?rhel}
cat kdump.list subscriptions.list sosreport.list networkmanager.list selinux.list >> system.list
%endif

%find_lang %{name}

# dwz has trouble with the go binaries
# https://fedoraproject.org/wiki/PackagingDrafts/Go
%global _dwz_low_mem_die_limit 0

%define find_debug_info %{_rpmconfigdir}/find-debuginfo.sh %{?_missing_build_ids_terminate_build:--strict-build-id} %{?_include_minidebuginfo:-m} %{?_find_debuginfo_dwz_opts} %{?_find_debuginfo_opts} "%{_builddir}/%{?buildsubdir}"

# Redefine how debug info is built to slip in our extra debug files
%define __debug_install_post   \
   %{find_debug_info} \
   cat debug.partial >> %{_builddir}/%{?buildsubdir}/debugfiles.list \
%{nil}

# -------------------------------------------------------------------------------
# Sub-packages

%package bridge
Summary: Cockpit bridge server-side component
Obsoletes: %{name}-daemon < 0.48-2
Requires: glib-networking
Requires: polkit

%description bridge
The Cockpit bridge component installed server side and runs commands on the
system on behalf of the web based user interface.

%files bridge -f base.list
%{_datadir}/%{name}/base1/bundle.min.js.gz
%doc %{_mandir}/man1/cockpit-bridge.1.gz
%{_bindir}/cockpit-bridge
%{_libexecdir}/cockpit-askpass

%package doc
Summary: Cockpit deployment and developer guide

%description doc
The Cockpit Deployment and Developer Guide shows sysadmins how to
deploy Cockpit on their machines as well as helps developers who want to
embed or extend Cockpit.

%files doc
%exclude %{_docdir}/%{name}/AUTHORS
%exclude %{_docdir}/%{name}/COPYING
%exclude %{_docdir}/%{name}/README.md
%{_docdir}/%{name}

%package machines
Summary: Cockpit user interface for virtual machines
Requires: %{name}-bridge >= %{required_base}
Requires: %{name}-system >= %{required_base}
Requires: libvirt
Requires: libvirt-client

%description machines
The Cockpit components for managing virtual machines.

%files machines -f machines.list

%package ostree
Summary: Cockpit user interface for rpm-ostree
# Requires: Uses new translations functionality
Requires: %{name}-bridge >= %{required_base}
Requires: %{name}-system >= %{required_base}
%if 0%{?fedora} > 0 && 0%{?fedora} < 24
Requires: rpm-ostree >= 2015.10-1
%else
Requires: /usr/libexec/rpm-ostreed
%endif

%description ostree
The Cockpit components for managing software updates for ostree based systems.

%files ostree -f ostree.list

%package pcp
Summary: Cockpit PCP integration
Requires: %{name}-bridge = %{version}-%{release}
Requires: pcp

%description pcp
Cockpit support for reading PCP metrics and loading PCP archives.

%files pcp -f pcp.list
%{_libexecdir}/cockpit-pcp
%{_localstatedir}/lib/pcp/config/pmlogconf/tools/cockpit

%post pcp
# HACK - https://bugzilla.redhat.com/show_bug.cgi?id=1185764
# We can't use "systemctl reload-or-try-restart" since systemctl might
# be out of sync with reality.
/usr/share/pcp/lib/pmlogger condrestart

%if %{defined build_dashboard}
%package dashboard
Summary: Cockpit SSH remoting and dashboard
Requires: libssh >= %{libssh_version}
Requires: cockpit-ws = %{version}-%{release}
Provides: cockpit-ssh = %{version}-%{release}

%description dashboard
Cockpit support for remoting to other servers, bastion hosts, and a basic dashboard

%files dashboard -f dashboard.list
%{_libexecdir}/cockpit-ssh

%post dashboard
# HACK: Until policy changes make it downstream
# https://bugzilla.redhat.com/show_bug.cgi?id=1381331
test -f %{_bindir}/chcon && chcon -t cockpit_ws_exec_t %{_libexecdir}/cockpit-ssh
%endif

%package storaged
Summary: Cockpit user interface for storage, using Storaged
# Lock bridge dependency due to --with-storaged-iscsi-sessions
# which uses new less stable /manifests.js request path.
%if 0%{?rhel}
Requires: %{name}-bridge >= %{version}-%{release}
%endif
Requires: %{name}-shell >= %{required_base}
Requires: storaged >= 2.1.1
%if 0%{?fedora} >= 24 || 0%{?rhel} >= 8
Recommends: storaged-lvm2 >= 2.1.1
Recommends: storaged-iscsi >= 2.1.1
Recommends: device-mapper-multipath
%else
Requires: storaged-lvm2 >= 2.1.1
Requires: storaged-iscsi >= 2.1.1
Requires: device-mapper-multipath
%endif
BuildArch: noarch

%description storaged
The Cockpit component for managing storage.  This package uses Storaged.

%files storaged -f storaged.list

%package system
Summary: Cockpit admin interface package for configuring and troubleshooting a system
BuildArch: noarch
Requires: %{name}-bridge = %{version}-%{release}
Requires: shadow-utils
Requires: grep
Requires: libpwquality
Requires: /usr/bin/date
Provides: %{name}-assets
Obsoletes: %{name}-assets < 0.32
Provides: %{name}-realmd = %{version}-%{release}
Provides: %{name}-shell = %{version}-%{release}
Obsoletes: %{name}-shell < 127
Provides: %{name}-systemd = %{version}-%{release}
Provides: %{name}-tuned = %{version}-%{release}
Provides: %{name}-users = %{version}-%{release}
%if 0%{?rhel}
Provides: %{name}-networkmanager = %{version}-%{release}
Requires: NetworkManager
Provides: %{name}-kdump = %{version}-%{release}
Requires: kexec-tools
# Optional components (only when soft deps are supported)
%if 0%{?fedora} >= 24 || 0%{?rhel} >= 8
Recommends: NetworkManager-team
%endif
Provides: %{name}-selinux = %{version}-%{release}
Provides: %{name}-sosreport = %{version}-%{release}
Provides: %{name}-subscriptions = %{version}-%{release}
Requires: subscription-manager >= 1.13
%endif

%description system
This package contains the Cockpit shell and system configuration interfaces.

%files system -f system.list

%package tests
Summary: Tests for Cockpit
Requires: %{name}-bridge >= %{version}-%{release}
Requires: %{name}-shell >= %{version}-%{release}
Requires: openssh-clients
Provides: %{name}-test-assets
Obsoletes: %{name}-test-assets < 132

%description tests
This package contains tests and files used while testing Cockpit.
These files are not required for running Cockpit.

%files tests
%{_unitdir}/cockpit.service.d
%{_datadir}/%{name}/playground
%{_prefix}/lib/cockpit-test-assets

%package ws
Summary: Cockpit Web Service
Requires: glib-networking
Requires: openssl
Requires: glib2 >= 2.37.4
Obsoletes: cockpit-selinux-policy <= 0.83
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description ws
The Cockpit Web Service listens on the network, and authenticates users.

%files ws -f %{name}.lang
%doc %{_mandir}/man5/cockpit.conf.5.gz
%doc %{_mandir}/man8/cockpit-ws.8.gz
%doc %{_mandir}/man8/remotectl.8.gz
%doc %{_mandir}/man8/pam_ssh_add.8.gz
%config(noreplace) %{_sysconfdir}/%{name}/ws-certs.d
%config(noreplace) %{_sysconfdir}/pam.d/cockpit
%{_unitdir}/cockpit.service
%{_unitdir}/cockpit.socket
%{_prefix}/lib/firewalld/services/cockpit.xml
%{_sbindir}/remotectl
%{_libdir}/security/pam_ssh_add.so
%{_libexecdir}/cockpit-ws
%{_libexecdir}/cockpit-stub
%attr(4750, root, cockpit-ws) %{_libexecdir}/cockpit-session
%attr(775, -, wheel) %{_localstatedir}/lib/%{name}
%{_datadir}/%{name}/static
%{_datadir}/%{name}/branding

%pre ws
getent group cockpit-ws >/dev/null || groupadd -r cockpit-ws
getent passwd cockpit-ws >/dev/null || useradd -r -g cockpit-ws -d / -s /sbin/nologin -c "User for cockpit-ws" cockpit-ws

%post ws
%systemd_post cockpit.socket
# firewalld only partially picks up changes to its services files without this
test -f %{_bindir}/firewall-cmd && firewall-cmd --reload --quiet || true

%preun ws
%systemd_preun cockpit.socket

%postun ws
%systemd_postun_with_restart cockpit.socket
%systemd_postun_with_restart cockpit.service

# -------------------------------------------------------------------------------
# Conditional Sub-packages

%if 0%{?rhel} == 0

%package kdump
Summary: Cockpit user interface for kernel crash dumping
Requires: %{name}-bridge >= %{required_base}
Requires: %{name}-shell >= %{required_base}
Requires: kexec-tools
BuildArch: noarch

%description kdump
The Cockpit component for configuring kernel crash dumping.

%files kdump -f kdump.list

%package sosreport
Summary: Cockpit user interface for diagnostic reports
Requires: %{name}-bridge >= %{required_base}
Requires: %{name}-shell >= %{required_base}
Requires: sos
BuildArch: noarch

%description sosreport
The Cockpit component for creating diagnostic reports with the
sosreport tool.

%files sosreport -f sosreport.list

%package subscriptions
Summary: Cockpit subscription user interface package
Requires: %{name}-bridge >= %{required_base}
Requires: %{name}-shell >= %{required_base}
Requires: subscription-manager >= 1.13
BuildArch: noarch

%description subscriptions
This package contains the Cockpit user interface integration with local
subscription management.

%files subscriptions -f subscriptions.list

%package networkmanager
Summary: Cockpit user interface for networking, using NetworkManager
Requires: %{name}-bridge >= %{required_base}
Requires: %{name}-shell >= %{required_base}
Requires: NetworkManager
# Optional components (only when soft deps are supported)
%if 0%{?fedora} >= 24 || 0%{?rhel} >= 8
Recommends: NetworkManager-team
%endif
BuildArch: noarch

%description networkmanager
The Cockpit component for managing networking.  This package uses NetworkManager.

%files networkmanager -f networkmanager.list

%endif

%if 0%{?rhel}%{?centos} == 0

%package selinux
Summary: Cockpit SELinux package
Requires: %{name}-bridge >= %{required_base}
Requires: %{name}-shell >= %{required_base}
Requires: setroubleshoot-server >= 3.3.3
BuildArch: noarch

%description selinux
This package contains the Cockpit user interface integration with the
utility setroubleshoot to diagnose and resolve SELinux issues.

%files selinux -f selinux.list

%endif

%ifarch x86_64 %{arm} aarch64 ppc64le

%package docker
Summary: Cockpit user interface for Docker containers
Requires: %{name}-bridge >= %{required_base}
Requires: %{name}-shell >= %{required_base}
Requires: docker >= 1.3.0
Requires: python

%description docker
The Cockpit components for interacting with Docker and user interface.
This package is not yet complete.

%files docker -f docker.list

%endif

%ifarch x86_64 ppc64le

%package kubernetes
Summary: Cockpit user interface for Kubernetes cluster
Requires: /usr/bin/kubectl
# Requires: Needs newer localization support
Requires: %{name}-bridge >= %{required_base}
Requires: %{name}-shell >= %{required_base}
BuildRequires: golang-bin
BuildRequires: golang-src

%description kubernetes
The Cockpit components for visualizing and configuring a Kubernetes
cluster. Installed on the Kubernetes master. This package is not yet complete.

%files kubernetes -f kubernetes.list
%{_libexecdir}/cockpit-kube-auth
%{_libexecdir}/cockpit-kube-launch

%endif

# The changelog is automatically generated and merged
%changelog
