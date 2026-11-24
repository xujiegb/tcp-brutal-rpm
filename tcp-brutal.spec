%global upstream_name tcp-brutal

Name:           tcp-brutal-tools
Version:        2.0.1
Release:        1%{?dist}
%global dkms_version %{version}.%{release}
%global dkms_src %{_usrsrc}/%{upstream_name}-%{dkms_version}
Summary:        Userspace management utility for TCP Brutal
License:        GPL-3.0-only
URL:            https://github.com/HyNetworks/tcp-brutal
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{upstream_name}-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  bash
BuildRequires:  make
BuildRequires:  systemd-rpm-macros
BuildRequires:  sed
BuildRequires:  coreutils
Requires:       iproute

%description
brutalctl manages destination rules for the TCP Brutal congestion control
kernel module. It can be used with an independently installed module.

%package -n tcp-brutal
Summary:        TCP Brutal congestion control (complete installation)
BuildArch:      noarch
Requires:       tcp-brutal-dkms = %{version}-%{release}
Requires:       tcp-brutal-tools = %{version}-%{release}

%description -n tcp-brutal
Installs the TCP Brutal DKMS kernel module and the brutalctl management tool.

%package -n tcp-brutal-dkms
Summary:        TCP Brutal kernel module source for DKMS
BuildArch:      noarch
Requires:       dkms
Requires:       kernel-devel
Requires:       gcc
Requires:       make
Requires:       elfutils-libelf-devel
Requires:       kmod
Requires(post): dkms
Requires(preun): dkms
Requires(posttrans): dkms

%description -n tcp-brutal-dkms
Source code for the TCP Brutal congestion control module. DKMS builds it
against the installed kernel development files and rebuilds it on kernel
updates. No precompiled kernel module is shipped in this RPM.

%prep
%autosetup -n %{upstream_name}-%{version}

%build
%{__cc} %{build_cflags} -std=c99 -Wall -Wextra -o tools/brutalctl \
    tools/brutalctl.c %{build_ldflags}
PACKAGE_VERSION='%{dkms_version}' bash scripts/mkdkmsconf.sh > dkms.conf

%install
install -Dpm 0755 tools/brutalctl %{buildroot}%{_bindir}/brutalctl
install -d %{buildroot}%{dkms_src}/tools
install -pm 0644 dkms.conf Makefile brutal.h brutal_cc.c brutal_rules.c \
    brutal_sockopt.c .clang-format %{buildroot}%{dkms_src}/
install -pm 0644 tools/Makefile tools/brutalctl.c %{buildroot}%{dkms_src}/tools/
install -Dpm 0755 scripts/mkdkmsconf.sh %{buildroot}%{dkms_src}/scripts/mkdkmsconf.sh
install -d %{buildroot}%{_modulesloaddir}
printf 'brutal\n' > %{buildroot}%{_modulesloaddir}/tcp-brutal.conf

%check
bash -n dkms.conf
grep -Fx 'PACKAGE_NAME="tcp-brutal"' dkms.conf
grep -Fx 'PACKAGE_VERSION="%{dkms_version}"' dkms.conf
grep -Fx 'AUTOINSTALL="yes"' dkms.conf
test -x tools/brutalctl

%post -n tcp-brutal-dkms
if ! dkms add -m '%{upstream_name}' -v '%{dkms_version}' --rpm_safe_upgrade; then
    echo 'Warning: TCP Brutal DKMS registration failed; inspect dkms status.' >&2
fi

%preun -n tcp-brutal-dkms
if ! dkms remove -m '%{upstream_name}' -v '%{dkms_version}' --all --rpm_safe_upgrade; then
    echo 'Warning: TCP Brutal DKMS removal failed; inspect dkms status.' >&2
fi

%posttrans -n tcp-brutal-dkms
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

%files -n tcp-brutal-dkms
%license LICENSE
%{dkms_src}/
%{_modulesloaddir}/tcp-brutal.conf

%changelog
* Tue Nov 24 2026 TCP Brutal RPM maintainers <packaging@example.invalid> - 2.0.1-1
- Initial COPR packaging for TCP Brutal 2.0.1.
