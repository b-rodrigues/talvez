let
 pkgs = import (fetchTarball "https://github.com/rstats-on-nix/nixpkgs/archive/2025-09-16.tar.gz") {};
 
  pypkgs = builtins.attrValues {
    inherit (pkgs.python313Packages) 
      griffe
      ipython
      mkdocs
      mkdocs-git-revision-date-localized-plugin
      mkdocs-material
      mkdocstrings-python
      numpy
      pytest
      ;
  };

  rpkgs = builtins.attrValues {
    inherit (pkgs.rPackages) 
      maybe
      ;
  };

  system_packages = builtins.attrValues {
    inherit (pkgs) 
      pyright
      ispell
      glibcLocales
      glibcLocalesUtf8
      nix
      pandoc
      python313
      R;
  };
  
in

pkgs.mkShell {
  LOCALE_ARCHIVE = if pkgs.system == "x86_64-linux" then "${pkgs.glibcLocales}/lib/locale/locale-archive" else "";
  LANG = "en_US.UTF-8";
   LC_ALL = "en_US.UTF-8";
   LC_TIME = "en_US.UTF-8";
   LC_MONETARY = "en_US.UTF-8";
   LC_PAPER = "en_US.UTF-8";
   LC_MEASUREMENT = "en_US.UTF-8";
   RETICULATE_PYTHON = "${pkgs.python313}/bin/python";

  buildInputs = [ rpkgs pypkgs system_packages ];

  shellHook = ''
    export PYTHONPATH=$PWD/src:$PYTHONPATH
  '';
  
}