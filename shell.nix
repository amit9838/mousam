# source: https://gist.github.com/cdepillabout/f7dbe65b73e1b5e70b7baa473dafddb3

let
  # use unstable branch for latest versions
  nixpkgs-src = builtins.fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-unstable";

  pkgs = import nixpkgs-src { config = { allowUnfree = false; }; };

  # python version
  myPython = pkgs.python3;

  pythonWithPkgs = myPython.withPackages (pythonPkgs: with pythonPkgs; [
    #black
    ipython
    meson
    ninja
    pip
    pygobject3
    requests
    setuptools
    virtualenvwrapper
    wheel
  ]);

  shell = pkgs.mkShell {
    buildInputs = with pkgs; [
      # python version with packages from above
      pythonWithPkgs

      # formatter for this file
      nixpkgs-fmt

      # meson
      appstream-glib
      cmake
      desktop-file-utils
      gettext
      glib
      gobject-introspection
      gtk4
      libglibutil
      librsvg
      pkg-config
    ];

    shellHook = ''
      # allow the use of wheels
      SOURCE_DATE_EPOCH=$(date +%s)

      # setup the virtual environment if it does not already exist
      VENV=.venv
      if test ! -d $VENV; then
        virtualenv $VENV
      fi
      source ./$VENV/bin/activate
      export PYTHONPATH=`pwd`/$VENV/${myPython.sitePackages}/:$PYTHONPATH

      pip install --disable-pip-version-check pygobject
      pip install --disable-pip-version-check requests

      # path to compiled schemas: https://stackoverflow.com/questions/28953925/glib-gio-error-no-gsettings-schemas-are-installed-on-the-system
      export XDG_DATA_DIRS=`pwd`/compiledir/share/
    '';
  };
in

shell
