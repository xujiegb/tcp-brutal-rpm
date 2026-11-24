# TCP Brutal RPM packaging

Standalone packaging repository for HyNetworks/tcp-brutal v2.0.1.
The source RPM is named `tcp-brutal-tools` so that the compiled tool is native
architecture and the `tcp-brutal` metapackage and `tcp-brutal-dkms` subpackage
can both be noarch.

## Supported COPR build targets

Both pull requests and default-branch commits build the same 14 targets:

| Distribution | x86_64 | aarch64 | ppc64le | s390x | riscv64 |
|---|---|---|---|---|---|
| Fedora 44 | Yes | Yes | Yes | Yes | Yes |
| Fedora 45 | Yes | Yes | Yes | Yes | Yes |
| RHEL 10 + EPEL | Yes | Yes | Yes | Yes | Not available |

RHEL uses `rhel+epel-10-*`, not `epel-10-*` (CentOS Stream-based).
RHEL 10 RISC-V is a developer preview; no matching public COPR chroot has
been confirmed. Fedora RISC-V uses the alternative architecture repositories.
The matrix is fixed: no Rawhide or moving Fedora aliases are selected.
Check current builder availability with `copr-cli list-chroots`.

## Build locally on Fedora

```sh
sudo dnf install rpm-build rpmdevtools packit mock
packit srpm
# Or without Packit:
rpmdev-setuptree
spectool -g -R tcp-brutal.spec
rpmbuild -bs tcp-brutal.spec
mock -r fedora-44-x86_64 --rebuild ~/rpmbuild/SRPMS/tcp-brutal-tools-*.src.rpm
```

## Packit service

Install the Packit GitHub App on this repository and open a PR. The default
branch commit job is persistent. For a custom COPR project, create it,
grant Packit permission, and add this GitHub repository in the project's
Packit allowed forge projects setting. Uncomment and replace the owner/project
fields in the commit job. The PR job remains isolated.

To update upstream, edit Version and reset Release to 1 in the spec; use a new
Release for packaging-only changes. Packit fetches exactly that upstream tag.
A release on the original upstream repository does not trigger this independent
repository. RPM builds have network disabled; source preparation fetches the
archive beforehand.

## Install and verify on Fedora or RHEL 10

On registered RHEL 10, enable CodeReady Builder and EPEL first:

```sh
sudo subscription-manager repos --enable "codeready-builder-for-rhel-10-$(arch)-rpms"
sudo dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-10.noarch.rpm
sudo dnf install dnf-plugins-core
```

For RHEL, explicitly select the matching chroot when enabling COPR:

```sh
sudo dnf copr enable YOUR_COPR_USERNAME/tcp-brutal "rhel+epel-10-$(arch)"
```

For Fedora, the default COPR repository selection is normally sufficient.
Run the common installation and verification steps below (skip the first line
if the correct RHEL COPR repository has already been enabled).

```sh
sudo dnf copr enable YOUR_COPR_USERNAME/tcp-brutal
sudo dnf install tcp-brutal
sudo dnf install "kernel-devel-$(uname -r)"
sudo dkms autoinstall -k "$(uname -r)"
sudo modprobe brutal
dkms status
modinfo brutal
sudo brutalctl list
```

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
