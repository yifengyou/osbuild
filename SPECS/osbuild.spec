%global         forgeurl https://github.com/osbuild/osbuild
%global         selinuxtype targeted

Version:              65

%forgemeta

%global         pypi_name osbuild
%global         pkgdir %{_prefix}/lib/%{pypi_name}

Name:                 %{pypi_name}
Release:              1%{?dist}.rocky.0.1
License:              ASL 2.0

URL:                  %{forgeurl}

Source0:              %{forgesource}
BuildArch:            noarch
Summary:              A build system for OS images


BuildRequires:        make
BuildRequires:        python3-devel
BuildRequires:        python3-docutils
BuildRequires:        systemd

Requires:             bash
Requires:             bubblewrap
Requires:             coreutils
Requires:             curl
Requires:             dnf
Requires:             e2fsprogs
Requires:             glibc
Requires:             policycoreutils
Requires:             qemu-img
Requires:             systemd
Requires:             tar
Requires:             util-linux
Requires:             python3-%{pypi_name} = %{version}-%{release}
Requires:             (%{name}-selinux if selinux-policy-%{selinuxtype})

# Turn off dependency generators for runners. The reason is that runners are
# tailored to the platform, e.g. on RHEL they are using platform-python. We
# don't want to pick up those dependencies on other platform.
%global __requires_exclude_from ^%{pkgdir}/(runners)/.*$

# Turn off shebang mangling on RHEL. brp-mangle-shebangs (from package
# redhat-rpm-config) is run on all executables in a package after the `install`
# section runs. The below macro turns this behavior off for:
#   - runners, because they already have the correct shebang for the platform
#     they're meant for, and
#   - stages and assemblers, because they are run within osbuild build roots,
#     which are not required to contain the same OS as the host and might thus
#     have a different notion of "platform-python".
# RHEL NB: Since assemblers and stages are not excluded from the dependency
# generator, this also means that an additional dependency on /usr/bin/python3
# will be added. This is intended and needed, so that in the host build root
# /usr/bin/python3 is present so stages and assemblers can be run.
%global __brp_mangle_shebangs_exclude_from ^%{pkgdir}/(assemblers|runners|stages)/.*$

%{?python_enable_dependency_generator}

%description
A build system for OS images

%package -n     python3-%{pypi_name}
Summary:              %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}

%description -n python3-%{pypi_name}
A build system for OS images

%package        lvm2
Summary:              LVM2 support
Requires:             %{name} = %{version}-%{release}
Requires:             lvm2

%description lvm2
Contains the necessary stages and device host
services to build LVM2 based images.

%package        luks2
Summary:              LUKS2 support
Requires:             %{name} = %{version}-%{release}
Requires:             cryptsetup

%description luks2
Contains the necessary stages and device host
services to build LUKS2 encrypted images.

%package        ostree
Summary:              OSTree support
Requires:             %{name} = %{version}-%{release}
Requires:             ostree
Requires:             rpm-ostree

%description ostree
Contains the necessary stages, assembler and source
to build OSTree based images.

%package        selinux
Summary:              SELinux policies
Requires:             %{name} = %{version}-%{release}
BuildRequires:        selinux-policy
BuildRequires:        selinux-policy-devel
%{?selinux_requires}

%description    selinux
Contains the necessary SELinux policies that allows
osbuild to use labels unknown to the host inside the
containers it uses to build OS artifacts.

%package        tools
Summary:              Extra tools and utilities
Requires:             %{name} = %{version}-%{release}
Requires:             python3-pyyaml

%description    tools
Contains additional tools and utilities for development of
manifests and osbuild.

%prep
%forgesetup
%{__cp} %{_builddir}/%{name}-%{version}/runners/org.osbuild.rhel87 %{_builddir}/%{name}-%{version}/runners/org.osbuild.rocky87
%{__cp} %{_builddir}/%{name}-%{version}/runners/org.osbuild.rhel91 %{_builddir}/%{name}-%{version}/runners/org.osbuild.rocky91
%{__cp} %{_builddir}/%{name}-%{version}/runners/org.osbuild.rhel91 %{_builddir}/%{name}-%{version}/runners/org.osbuild.rocky91

%build
%py3_build
make man

# SELinux
make -f /usr/share/selinux/devel/Makefile osbuild.pp
bzip2 -9 osbuild.pp

%pre
%selinux_relabel_pre -s %{selinuxtype}

%install
%py3_install

mkdir -p %{buildroot}%{pkgdir}/stages
install -p -m 0755 $(find stages -type f) %{buildroot}%{pkgdir}/stages/

mkdir -p %{buildroot}%{pkgdir}/assemblers
install -p -m 0755 $(find assemblers -type f) %{buildroot}%{pkgdir}/assemblers/

mkdir -p %{buildroot}%{pkgdir}/runners
install -p -m 0755 $(find runners -type f -or -type l) %{buildroot}%{pkgdir}/runners

mkdir -p %{buildroot}%{pkgdir}/sources
install -p -m 0755 $(find sources -type f) %{buildroot}%{pkgdir}/sources

mkdir -p %{buildroot}%{pkgdir}/devices
install -p -m 0755 $(find devices -type f) %{buildroot}%{pkgdir}/devices

mkdir -p %{buildroot}%{pkgdir}/inputs
install -p -m 0755 $(find inputs -type f) %{buildroot}%{pkgdir}/inputs

mkdir -p %{buildroot}%{pkgdir}/mounts
install -p -m 0755 $(find mounts -type f) %{buildroot}%{pkgdir}/mounts

# mount point for bind mounting the osbuild library
mkdir -p %{buildroot}%{pkgdir}/osbuild

# schemata
mkdir -p %{buildroot}%{_datadir}/osbuild/schemas
install -p -m 0644 $(find schemas/*.json) %{buildroot}%{_datadir}/osbuild/schemas
ln -s %{_datadir}/osbuild/schemas %{buildroot}%{pkgdir}/schemas

# documentation
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{_mandir}/man5
install -p -m 0644 -t %{buildroot}%{_mandir}/man1/ docs/*.1
install -p -m 0644 -t %{buildroot}%{_mandir}/man5/ docs/*.5

# SELinux
install -D -m 0644 -t %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype} %{name}.pp.bz2
install -D -m 0644 -t %{buildroot}%{_mandir}/man8 selinux/%{name}_selinux.8

# Udev rules
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0755 data/10-osbuild-inhibitor.rules %{buildroot}%{_udevrulesdir}

%check
exit 0
# We have some integration tests, but those require running a VM, so that would
# be an overkill for RPM check script.

%files
%license LICENSE
%{_bindir}/osbuild
%{_mandir}/man1/%{name}.1*
%{_mandir}/man5/%{name}-manifest.5*
%{_datadir}/osbuild/schemas
%{pkgdir}
%{_udevrulesdir}/*.rules
# the following files are in the lvm2 sub-package
%exclude %{pkgdir}/devices/org.osbuild.lvm2*
%exclude %{pkgdir}/stages/org.osbuild.lvm2*
# the following files are in the luks2 sub-package
%exclude %{pkgdir}/devices/org.osbuild.luks2*
%exclude %{pkgdir}/stages/org.osbuild.crypttab
%exclude %{pkgdir}/stages/org.osbuild.luks2*
# the following files are in the ostree sub-package
%exclude %{pkgdir}/assemblers/org.osbuild.ostree*
%exclude %{pkgdir}/inputs/org.osbuild.ostree*
%exclude %{pkgdir}/sources/org.osbuild.ostree*
%exclude %{pkgdir}/stages/org.osbuild.ostree*
%exclude %{pkgdir}/stages/org.osbuild.rpm-ostree

%files -n       python3-%{pypi_name}
%license LICENSE
%doc README.md
%{python3_sitelib}/%{pypi_name}-*.egg-info/
%{python3_sitelib}/%{pypi_name}/

%files lvm2
%{pkgdir}/devices/org.osbuild.lvm2*
%{pkgdir}/stages/org.osbuild.lvm2*

%files luks2
%{pkgdir}/devices/org.osbuild.luks2*
%{pkgdir}/stages/org.osbuild.crypttab
%{pkgdir}/stages/org.osbuild.luks2*

%files ostree
%{pkgdir}/assemblers/org.osbuild.ostree*
%{pkgdir}/inputs/org.osbuild.ostree*
%{pkgdir}/sources/org.osbuild.ostree*
%{pkgdir}/stages/org.osbuild.ostree*
%{pkgdir}/stages/org.osbuild.rpm-ostree

%files selinux
%{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2
%{_mandir}/man8/%{name}_selinux.8.*
%ghost %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/%{name}

%post selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2

%postun selinux
if [ $1 -eq 0 ]; then
    %selinux_modules_uninstall -s %{selinuxtype} %{name}
fi

%posttrans selinux
%selinux_relabel_post -s %{selinuxtype}

%files tools
%{_bindir}/osbuild-mpp


%changelog
* Sun Oct 02 2022 Release Engineering <releng@rockylinux.org> - 65-1.rocky.0.1
- Add Rocky Linux runners

* Fri Aug 26 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 65-1
- New upstream release

* Thu Aug 18 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 64-1
- New upstream release

* Wed Aug 03 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 63-1
- New upstream release

* Wed Jul 27 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 62-1
- New upstream release

* Wed Jul 20 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 61-1
- New upstream release

* Thu Jul 07 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 60-1
- New upstream release

* Wed Jun 22 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 59-1
- New upstream release

* Wed Jun 08 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 58-1
- New upstream release

* Thu May 26 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 57-1
- New upstream release

* Wed May 11 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 56-1
- New upstream release

* Wed Apr 27 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 55-1
- New upstream release

* Fri Apr 15 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 54-1
- New upstream release

* Thu Mar 24 2022 imagebuilder-bot <imagebuilder-bots+imagebuilder-bot@redhat.com> - 53-1
- New upstream release

* Tue Mar 08 2022 Simon Steinbeiss <simon.steinbeiss@redhat.com> - 52-1
- New upstream release

* Sun Feb 27 2022 Simon Steinbeiss <simon.steinbeiss@redhat.com> - 50-1
- New upstream release

* Wed Feb 23 2022 Simon Steinbeiss <simon.steinbeiss@redhat.com> - 49-1
- New upstream release

* Thu Feb 17 2022 Chloe Kaubisch <chloe.kaubisch@gmail.com> - 48-1
- New upstream release

* Thu Feb 03 2022 Jacob Kozol <jacobdkozol@gmail.com> - 47-1
- New upstream release

* Wed Jan 19 2022 Simon Steinbeiss <simon.steinbeiss@redhat.com> - 46-1
- New upstream release

* Mon Jan 10 2022 Tomas Hozza <thozza@redhat.com> - 45-1
- New upstream release

* Wed Jan 05 2022 Simon Steinbeiss <simon.steinbeiss@redhat.com> - 44-1
- New upstream release

* Wed Dec 01 2021 Achilleas Koutsou <achilleas@redhat.com> - 43-1
- New upstream release

* Mon Nov 29 2021 Ondřej Budai <ondrej@budai.cz> - 42-1
- New upstream release

* Fri Oct 15 2021 Achilleas Koutsou <achilleas@redhat.com> - 39-1
- New upstream release

* Sun Aug 29 2021 Tom Gundersen <teg@jklm.no> - 35-1
- Upstream release 35

* Sun Aug 29 2021 Tom Gundersen <teg@jklm.no> - 34-1
- Upstream release 34

* Wed Aug 25 2021 Tom Gundersen <teg@jklm.no> - 33-1
- Upstream release 33

* Tue Aug 24 2021 Tom Gundersen <teg@jklm.no> - 32-1
- Upstream release 32

* Mon Aug 23 2021 Tom Gundersen <teg@jklm.no> - 31-1
- Upstream release 31

* Fri Jul 23 2021 Christian Kellner <christian@kellner.me> - 30-1
- Upstream release 30
- Ship osbuild-mpp in new tools sub-package.
- Remove executable bit from schemata files.

* Tue Apr 27 2021 Achilleas Koutsou <achilleas@redhat.com> - 28-1
- Upstream release 28
- Includes fixes and feature additions for multiple stages.

* Fri Feb 19 2021 Christian Kellner <ckellner@redhat.com> - 26-1
- Upstream release 26
- Includes the necessary stages to build boot isos.

* Fri Feb 12 2021 Christian Kellner <ckellner@redhat.com> - 25-1
- Upstream 25 release
- First tech preview of the new manifest format. Includes
  various new stages and inputs to be able to build ostree
  commits contained in a oci archive.

* Thu Jan 28 2021 Christian Kellner <ckellner@redhat.com> - 24-1
- Upstream 24 release
- Include new `Input` modules.

* Mon Nov 23 2020 Christian Kellner <ckellner@redhat.com> - 23-3
- only disable the dep. generator for runners, remove explicity
  python3 requirement again. The dependency should be picked up
  via the dependency generator now.

* Fri Nov 13 2020 Christian Kellner <ckellner@redhat.com> - 23-2
- Explicilty require python3. See the comment above the Requires
  for an explanation why this is needed.

* Fri Oct 23 2020 Christian Kellner <ckellner@redhat.com> - 23-1
- Upstream release 23
- Do not mangle shebangs for assemblers, runners & stages.

* Wed Oct 14 2020 Christian Kellner <ckellner@redhat.com> - 22-1
- Upstream release 22
- Remove all patches since they are all in osbuild-22.
- bubblewrap replaced systemd-nspawn for sandboxing; change the
  requirements accordingly.

* Thu Aug 13 2020 Christian Kellner <ckellner@redhat.com> - 18-3
- Add patch to allow nnp and nosuid domain transitions
  https://github.com/osbuild/osbuild/pull/495

* Fri Jun 26 2020 Christian Kellner <ckellner@redhat.com> - 18-2
- Add patch to not pass floats to curl in the files source
  https://github.com/osbuild/osbuild/pull/459

* Tue Jun 23 2020 Christian Kellner <ckellner@redhat.com> - 18-1
- Upstream release 18
- All RHEL runners now use platform-python.

* Wed Jun 10 2020 Christian Kellner <ckellner@redhat.com> - 17-1
- Upstream release 17
- Add custom SELinux policy that lets osbuild set labels inside
  the build root that are unknown to the host.

* Thu Jun  4 2020 Christian Kellner <christian@kellner.me> - 16-1
- Upstream release 16
- Drop sources-fix-break-when-secrets-is-None.patch included in
  osbuild-16.

* Tue May 26 2020 Christian Kellner <ckellner@redhat.com> - 15-2
- Add a patch to allow org.osbuild.files source in the new format
  but without actually containing the secrets key.
  Taken from merged PR: https://github.com/osbuild/osbuild/pull/416

* Thu May 21 2020 Christian Kellner <ckellner@redhat.com> - 15-1
- New upstream release 15
- Drop draft4-validator.json patch, included in osbuild-15

* Wed May 13 2020 Christian Kellner <ckellner@redhat.com> - 14-2
- Add draft4-validator.json patch
  python3-jsonschema in RHEL currently has version 2.6.0 which
  has support validating up to and including draft4 of jsonschema.
  See https://github.com/osbuild/osbuild/pull/394

* Wed May 13 2020 Christian Kellner <ckellner@redhat.com> - 14-1
- Upstream release 14
- Install schemata to <datadir>/osbuild/schemas and include a
  symlink to it in /usr/lib/osbuild/schemas
- The directories /usr/lib/osbuild/{assemblers, stages}/osbuild
  got removed. Changes to osbuild made them obsolete.

* Wed Apr 15 2020 Christian Kellner <ckellner@redhat.com> - 12-1
- Sync with Fedora and use upstream release 12
- Specify the exact version in the 'python3-osbuild' requirement
  to avoid the library and the main binary being out of sync.
- osbuild-ostree sub-package with the necessary bits to create
  OSTree based images
- Turn off dependency generator for internal components
- Add NEWS.md file with the release notes and man pages

* Mon Dec 16 2019 Lars Karlitski <lars@karlitski.net> - 7-1
- New upstream release

* Sun Dec 1 2019 Tom Gundersen <teg@jklm.no> - 6-2
- New upstream release

* Thu Oct 24 2019 Lars Karlitski <lueberni@redhat.com> - 3-2
- add gating infra and tests

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 1-3
- Rebuilt for Python 3.8

* Mon Jul 29 2019 Martin Sehnoutka <msehnout@redhat.com> - 1-2
- update upstream URL to the new Github organization

* Wed Jul 17 2019 Martin Sehnoutka <msehnout@redhat.com> - 1-1
- Initial package
