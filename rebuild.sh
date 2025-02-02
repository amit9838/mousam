rm -rf builddir
meson setup -Dprefix=$HOME/.local builddir
meson compile -C builddir --verbose
meson install -C builddir
mousam