%bcond_with check

# Exclude input files from mangling
%global __brp_mangle_shebangs_exclude_from ^/usr/src/.*$

%global crate zed
%global app_id dev.zed.Zed

%global rustflags_debuginfo 0

Name:           zed-nomotion
Version:         0.209.7
Release:        1%?dist
Summary:        The Zed editor, patched to reduce power consumption
SourceLicense:  AGPL-3.0-only AND Apache-2.0 AND GPL-3.0-or-later
License:        ((Apache-2.0 OR MIT) AND BSD-3-Clause) AND ((MIT OR Apache-2.0) AND Unicode-3.0) AND (0BSD OR MIT OR Apache-2.0) AND (Apache-2.0 AND ISC) AND AGPL.3.0-only AND AGPL-3.0-or-later AND (Apache-2.0 OR BSL-1.0 OR MIT) AND (Apache-2.0 OR BSL-1.0) AND (Apache-2.0 OR ISC OR MIT) AND (Apache-2.0 OR MIT) AND (Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT) AND (Apache-2.0 WITH LLVM-exception) AND Apache-2.0 AND (BSD-2-Clause OR Apache-2.0 OR MIT) AND (BSD-2-Clause OR MIT OR Apache-2.0) AND BSD-2-Clause AND (CC0-1.0 OR Apache-2.0 OR Apache-2.0 WITH LLVM-exception) AND (CC0-1.0 OR Apache-2.0) AND (CC0-1.0 OR MIT-0 OR Apache-2.0) AND CC0-1.0 AND GPL-3.0-or-later AND (ISC AND (Apache-2.0 OR ISC) AND OpenSSL) AND (ISC AND (Apache-2.0 OR ISC)) AND ISC AND (MIT AND (MIT OR Apache-2.0)) AND (MIT AND BSD-3-Clause) AND (MIT OR Apache-2.0 OR CC0-1.0) AND (MIT OR Apache-2.0 OR NCSA) AND (MIT OR Apache-2.0 OR Zlib) AND (MIT OR Apache-2.0) AND (MIT OR Zlib OR Apache-2.0) AND MIT AND MPL-2.0 AND Unicode-3.0 AND (Unlicense OR MIT) AND (Zlib OR Apache-2.0 OR MIT) AND Zlib
URL:            https://zed.dev/
Source0:        https://github.com/zed-industries/zed/archive/refs/tags/v%{version}.tar.gz
Patch0:         disable-promotion-hack.patch

Conflicts:      zed
Conflicts:      zed-nightly
Conflicts:      zed-preview

BuildRequires:  libedit
BuildRequires:  cargo-rpm-macros >= 26
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  gettext-envsubst
BuildRequires:  clang
BuildRequires:  cmake
BuildRequires:  mold
BuildRequires:  alsa-lib-devel
BuildRequires:  fontconfig-devel
BuildRequires:  wayland-devel
BuildRequires:  libxkbcommon-x11-devel
BuildRequires:  openssl-devel
BuildRequires:  openssl-devel-engine
BuildRequires:  libzstd-devel
BuildRequires:  perl-FindBin
BuildRequires:  perl-IPC-Cmd
BuildRequires:  perl-File-Compare
BuildRequires:  perl-File-Copy
BuildRequires:  perl-lib
BuildRequires:  vulkan-loader
BuildRequires:  libcurl-devel

%description
Code at the speed of thought - Zed is a high-performance, multiplayer code editor from the creators of Atom and Tree-sitter. Patched for significantly reduced power consumption.

%prep
%autosetup -n %{crate}-%{version} -p1
%{__cargo} vendor > config.toml.vendor
%cargo_prep -N
cat config.toml.vendor >> .cargo/config.toml
rm config.toml.vendor

export DO_STARTUP_NOTIFY="true"
export APP_ID="%app_id"
export APP_ICON="%app_id"
export APP_NAME="Zed Editor"
export APP_CLI="zed"
export APP="%{_libexecdir}/zed-editor"
export APP_ARGS="%U"
export ZED_UPDATE_EXPLANATION="Run dnf up to update Zed from COPR."
export ZED_RELEASE_CHANNEL=stable
export BRANDING_LIGHT="#e9aa6a"
export BRANDING_DARK="#1a5fb4"

echo "StartupWMClass=$APP_ID" >> crates/zed/resources/zed.desktop.in
envsubst < "crates/zed/resources/zed.desktop.in" > $APP_ID.desktop # from https://aur.archlinux.org/cgit/aur.git/tree/PKGBUILD?h=zed-git#n52

envsubst < "crates/zed/resources/flatpak/zed.metainfo.xml.in" > $APP_ID.metainfo.xml

%build
export ZED_UPDATE_EXPLANATION="Run dnf up to update Zed from COPR."
echo "stable" > crates/zed/RELEASE_CHANNEL

%cargo_build -- --package zed --package cli

# generate-licenses fails if it can't get at crates.io directly
rm .cargo/config.toml
ALLOW_MISSING_LICENSES=1 script/generate-licenses

%install
install -Dm755 target/rpm/zed %{buildroot}%{_libexecdir}/zed-editor
install -Dm755 target/rpm/cli %{buildroot}%{_bindir}/zed

%__cargo clean

install -Dm644 %app_id.desktop %{buildroot}%{_datadir}/applications/%app_id.desktop
install -Dm644 crates/zed/resources/app-icon.png %{buildroot}%{_datadir}/pixmaps/%app_id.png

install -Dm644 %app_id.metainfo.xml %{buildroot}%{_metainfodir}/%app_id.metainfo.xml

# The license generation script doesn't generate licenses for ALL compiled dependencies, just direct deps of Zed, and it does not "group" licenses
# Zed also needs a special approach to fetch the dep licenses
%{__cargo} tree                                                             \
    -Z avoid-dev-deps                                                       \
    --workspace                                                             \
    --edges no-build,no-dev,no-proc-macro                                   \
    --target all                                                            \
    %{__cargo_parse_opts %{-n} %{-a} %{-f:-f%{-f*}}}                        \
    --prefix none                                                           \
    --format "{l}: {p}"                                                     \
    | sed -e "s: ($(pwd)[^)]*)::g" -e "s: / :/:g" -e "/\/.*:/{s/\// OR /}"  \
    | sed -e '/.*(\*).*/d' -e '/^: pet/ s/./MIT&/'                          \
    | sort -u                                                               \
> LICENSE.dependencies
mv assets/icons/LICENSES LICENSE.icons
mv assets/themes/LICENSES LICENSE.themes
mv assets/fonts/ibm-plex-sans/license.txt LICENSE.fonts

%if %{with check}
%check
%cargo_test
%endif

%files
%doc CODE_OF_CONDUCT.md
%doc README.md
%license LICENSE-AGPL
%license LICENSE-APACHE
%license LICENSE-GPL
%license LICENSE.dependencies
%license LICENSE.fonts
%license LICENSE.icons
%license LICENSE.themes
%license assets/licenses.md
%{_libexecdir}/zed-editor
%_bindir/zed
%{_datadir}/applications/%app_id.desktop
%{_datadir}/pixmaps/%app_id.png
%{_metainfodir}/%app_id.metainfo.xml

%changelog
%autochangelog
