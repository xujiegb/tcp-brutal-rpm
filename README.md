# TCP Brutal RPM packaging

Standalone packaging repository for HyNetworks/tcp-brutal.
One SPEC produces two independent binary packages: `tcp-brutal` (noarch)
contains DKMS kernel module sources and `brutalctl` (native architecture)
contains `/usr/bin/brutalctl`. The source RPM is named `brutalctl`.
Neither binary package requires the other for installation. To use brutalctl,
a compatible TCP Brutal 2.x kernel module must already be loaded. The tool
uses /proc/net/tcp_brutal/rules and the ip command to manage destination-based
bandwidth rules, shared rate groups and IPv4/IPv6 routes. It is not a DKMS,
module-loading or software-update utility. The module package replaces the
previous `tcp-brutal-dkms` package; `brutalctl` replaces the previous
`tcp-brutal-tools` package. RPM debuginfo packages may also be generated.

## Supported COPR build targets

Only published releases trigger builds across these 23 targets:

| Distribution | x86_64 | aarch64 | ppc64le | s390x | riscv64 |
|---|---|---|---|---|---|
| Fedora 43 | Yes | Yes | Yes | Yes | Yes |
| Fedora 44 | Yes | Yes | Yes | Yes | Yes |
| Fedora 45 | Yes | Yes | Yes | Yes | Yes |
| RHEL 10 | Yes | Yes | Yes | Yes | Not available |
| EPEL 10 | Yes | Yes | Yes | Yes | Not available |

RHEL uses the pure `rhel-10-*` chroots; EPEL uses separate `epel-10-*`
chroots (CentOS Stream-based). No combined RHEL and EPEL chroot is selected.
DKMS is a runtime dependency, not a build dependency. On RHEL, install it
from EPEL at deployment time. RHEL 10 and EPEL 10 do not have confirmed
riscv64 chroots; Fedora RISC-V uses the alternative architecture repositories.
The matrix is fixed: no Rawhide or moving Fedora aliases are selected.
Check current builder availability with `copr-cli list-chroots`.

## Build locally on Fedora

```sh
sudo dnf install rpm-build rpmdevtools packit mock
packit srpm
rpmdev-setuptree
spectool -g -R tcp-brutal.spec
rpmbuild -bs tcp-brutal.spec
mock -r fedora-44-x86_64 --rebuild ~/rpmbuild/SRPMS/brutalctl-*.src.rpm
```

## Packit service

Install the Packit GitHub App on this repository. Published releases build in
[repobot/tcp-brutal](https://copr.fedorainfracloud.org/coprs/repobot/tcp-brutal/).
Grant Packit builder permission in the COPR project and add
`github.com/xujiegb/tcp-brutal-rpm` to its Packit allowed forge projects setting.
Enable the required chroots in the COPR project. Pull requests and ordinary commits do not trigger builds.

To update upstream, edit Version and reset Release to 1 in the spec; use a new
Release for packaging-only changes. Packit fetches exactly that upstream tag using the SPEC Version, not the
packaging repository's release tag. Source preparation checks the archive for
kernel and management-tool sources and preserves the SPEC Version and Release.
A release on the original upstream repository does not trigger this independent
repository. RPM builds have network disabled; source preparation fetches the
archive beforehand.

## Manual GitHub Actions

Both workflows use the built-in GitHub Actions token with `contents: write`.
No additional repository secret is required. Repository and branch rules must
allow the workflow to write commits, tags and releases.

In the Actions tab, select the `main` branch:

- **Update SPEC Version**: enters an upstream version and RPM release, verifies
  the upstream tag, updates Version and Release using Bash and sed, replaces the single changelog
  entry instead of appending history, and commits only the SPEC to main. It does not publish a release.
- **Build RPM**: reads the current SPEC from main and publishes a GitHub release
  named `v<version>-<release>`, pointing to the exact packaging commit.
  Packit listens for the release event and submits the 23 COPR builds.
  For example, RPM version 2.0.1-2 uses the packaging tag `v2.0.1-2`
  and the upstream source tag `v2.0.1`.

The workflow does not overwrite existing releases or tags. To rebuild the same
release, retry the Packit check or post `/packit build --release v2.0.1-2` on
the release's commit. Increment Release for packaging changes. Publishing a
GitHub release does not itself mean the RPM builds have succeeded; check COPR.

A release can also be published manually in GitHub using a tag pointing to a
commit containing the release-trigger configuration. Ordinary main-branch
commits do not publish RPMs to the official COPR project.

## Install and verify on Fedora or RHEL 10

On registered RHEL 10, enable CodeReady Builder and EPEL first:

```sh
sudo subscription-manager repos --enable "codeready-builder-for-rhel-10-$(arch)-rpms"
sudo dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-10.noarch.rpm
sudo dnf install dnf-plugins-core
```

For RHEL, explicitly select the matching chroot when enabling COPR:

```sh
sudo dnf copr enable repobot/tcp-brutal "rhel-10-$(arch)"
```

For EPEL 10, select its separate chroot:

```sh
sudo dnf copr enable repobot/tcp-brutal "epel-10-$(arch)"
```

For Fedora, the default COPR repository selection is normally sufficient.
Run the common installation and verification steps below (skip the first line
if the correct RHEL or EPEL COPR repository has already been enabled).

```sh
sudo dnf copr enable repobot/tcp-brutal
sudo dnf install tcp-brutal
sudo dnf install "kernel-devel-$(uname -r)"
sudo dkms autoinstall -k "$(uname -r)"
sudo modprobe brutal
dkms status
modinfo brutal
```

Install the optional management utility separately (after loading the module):

```sh
sudo dnf install brutalctl
sudo brutalctl list
sudo brutalctl add 203.0.113.5/32 100
sudo brutalctl del 203.0.113.5/32
```

The example configures a shared target rate of 100 Mbps for connections to a
destination; choose a rate appropriate for the path. Rules do not persist
across reboot. The module also supports applications that configure their own
sockets, without requiring brutalctl. DNF handles RPM updates and removal.

No global congestion control change is made. Module loading is configured for
boot via modules-load.d. Upgrading the RPM does not forcibly reload the running
module. Reboot after a module upgrade to activate the new version. Secure Boot
requires a trusted DKMS signing key; follow Fedora/DKMS enrollment instructions.
For a Clang-built custom kernel install `clang`, `lld`, `llvm` first.

If you previously used the upstream installer, stop traffic relying on Brutal,
then use its documented uninstall command before migrating. Do not use both
installation mechanisms concurrently. The package will not delete an unrelated
installation's `/usr/local/bin/brutalctl` or DKMS source files.

## Validation

COPR compilation, DKMS build/load, Secure Boot, kernel upgrade and package
upgrade/erase must be tested on Fedora and RHEL 10 before production deployment.
The tool build does not validate the kernel module against every kernel or
architecture.
