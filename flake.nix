{
  description = "A automated script to fill reports for Explorhino";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        url = "nixpkgs/nixos-24.11";
      };

      deps = with pkgs; [
        #put dependencies here :)
      	python311
	imagemagick
      ] ++ (with pkgs.python311Packages; [
	pillow
      ]);

      non-deps = with pkgs; [
        #anything not dependency, but usefull (like editors)
      ];

      #put build instructions here :)
      explorhino-logger = pkgs.python311Packages.buildPythonApplication {
        name = "explorhino-logger";
        src = ./.;
        doCheck = false;
        propagatedBuildInputs = deps;
      };

    in
    {
      #give me a shell
      devShells.${system}.default = pkgs.mkShell {
        packages = deps ++ non-deps;
        buildInputs = deps;
        LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath deps;
      };
      packages.${system}.default = pkgs.writeShellScriptBin "explorhino-logger" ''
            ${explorhino-logger}/bin/main.py "''${@:1}"
          '';
    };
}
