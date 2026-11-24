%global upstream_name tcp-brutal

Name:           brutalctl
Version:        2.0.1
Release:        2%{?dist}
%global dkms_version %{version}.%{release}
%global dkms_src %{_usrsrc}/%{upstream_name}-%{dkms_version}
Summary:        TCP Brutal destination rule management utility
License:        GPL-3.0-only
URL:            https://github.com/HyNetworks/tcp-brutal
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{upstream_name}-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  glibc-devel
BuildRequires:  bash
BuildRequires:  make
BuildRequires:  systemd-rpm-macros
BuildRequires:  sed
BuildRequires:  coreutils
Requires:       iproute
Provides:       tcp-brutal-tools = %{version}-%{release}
Obsoletes:      tcp-brutal-tools < %{version}-%{release}

%description
brutalctl manages destination-based rate limits and shared bandwidth groups
through /proc/net/tcp_brutal/rules. It uses iproute to configure IPv4 and IPv6
routes selecting TCP Brutal and can list, add, delete or flush rules.
The TCP Brutal 2.x kernel module must be loaded to use these commands.
The utility does not install, update, load or rebuild the kernel module.

%package -n tcp-brutal
Summary:        TCP Brutal kernel module source for DKMS
BuildArch:      noarch
Provides:       tcp-brutal-dkms = %{version}-%{release}
Obsoletes:      tcp-brutal-dkms < %{version}-%{release}
Requires:       dkms
Requires:       kernel-devel >= 5.10
Requires:       gcc
Requires:       make
Requires:       elfutils-libelf-devel
Requires:       kmod
Requires(post): dkms
Requires(preun): dkms
Requires(posttrans): dkms

%description -n tcp-brutal
TCP Brutal is a Linux TCP congestion control algorithm supporting application
socket configuration and destination-based shared bandwidth groups. DKMS
builds the module against installed kernel development files and rebuilds it
on kernel updates. Linux 5.10 or later is required. The separate brutalctl
utility is optional; applications can configure the module directly.
No precompiled kernel module is shipped in this RPM.

%prep
%autosetup -n %{upstream_name}-%{version}
test -f brutal_cc.c
test -f tools/brutalctl.c

%build
%{__cc} %{build_cflags} -std=c99 -Wall -Wextra -o tools/brutalctl \
    tools/brutalctl.c %{build_ldflags}
PACKAGE_VERSION='%{dkms_version}' bash scripts/mkdkmsconf.sh > dkms.conf

%install
install -Dpm 0755 tools/brutalctl %{buildroot}%{_bindir}/brutalctl
install -d %{buildroot}%{dkms_src}
install -pm 0644 dkms.conf Makefile brutal.h brutal_cc.c brutal_rules.c \
    brutal_sockopt.c .clang-format %{buildroot}%{dkms_src}/
install -Dpm 0755 scripts/mkdkmsconf.sh %{buildroot}%{dkms_src}/scripts/mkdkmsconf.sh
install -d %{buildroot}%{_modulesloaddir}
printf 'brutal\n' > %{buildroot}%{_modulesloaddir}/tcp-brutal.conf

%check
bash -n dkms.conf
grep -Fx 'PACKAGE_NAME="tcp-brutal"' dkms.conf
grep -Fx 'PACKAGE_VERSION="%{dkms_version}"' dkms.conf
grep -Fx 'AUTOINSTALL="yes"' dkms.conf
test -x tools/brutalctl
status=0
tools/brutalctl > brutalctl-usage.txt 2>&1 || status=$?
test "$status" -eq 2
grep -F 'brutalctl list' brutalctl-usage.txt
grep -F 'brutalctl add' brutalctl-usage.txt
grep -F 'brutalctl del' brutalctl-usage.txt
grep -F 'brutalctl flush' brutalctl-usage.txt

%post -n tcp-brutal
if ! dkms add -m '%{upstream_name}' -v '%{dkms_version}' --rpm_safe_upgrade; then
    echo 'Warning: TCP Brutal DKMS registration failed; inspect dkms status.' >&2
fi

%preun -n tcp-brutal
if ! dkms remove -m '%{upstream_name}' -v '%{dkms_version}' --all --rpm_safe_upgrade; then
    echo 'Warning: TCP Brutal DKMS removal failed; inspect dkms status.' >&2
fi

%posttrans -n tcp-brutal
for module_dir in /usr/lib/modules/*; do
    [ -f "$module_dir/build/Makefile" ] || continue
    kernel=${module_dir##*/}
    if ! dkms install -m '%{upstream_name}' -v '%{dkms_version}' -k "$kernel"; then
        echo "Warning: TCP Brutal DKMS build/install failed for $kernel." >&2
    fi
done
exit 0

%files
%license LICENSE
%doc README.md README.zh.md
%{_bindir}/brutalctl

%files -n tcp-brutal
%license LICENSE
%doc README.md README.zh.md
%{dkms_src}/
%{_modulesloaddir}/tcp-brutal.conf

%changelog
* Tue Nov 24 2026 TCP Brutal RPM maintainers <packaging@example.invalid> - 2.0.1-2
- Split tcp-brutal and brutalctl into independent packages.
- Specify the userspace tool dependencies and validate its command interface.
- Fix Packit source preparation.

* Tue Nov 24 2026 TCP Brutal RPM maintainers <packaging@example.invalid> - 2.0.1-1
- Initial COPR packaging for TCP Brutal 2.0.1.
