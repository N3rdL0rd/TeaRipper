# Usage

## `teacx.py`

```plaintext
usage: teacx.py [-h] {deserialise,serialise} ...

Parse, serialise, and deserialise Tea for God .cx files

positional arguments:
  {deserialise,serialise}
    deserialise         Deserialise a cx file
    serialise           Serialise a file to cx

options:
  -h, --help            show this help message and exit

usage: teacx.py deserialise [-h] [-j] [-o OUTPUT] file

positional arguments:
  file                  path to the .cx file

options:
  -h, --help            show this help message and exit
  -j, --json            output as JSON
  -o OUTPUT, --output OUTPUT
                        path to the output file (default: original filename with changed extension)

usage: teacx.py serialise [-h] [-j] [-o OUTPUT] [-H HEADER_TEXT] [--original-path ORIGINAL_PATH] [--build-number BUILD_NUMBER] [--cx-version CX_VERSION] file

positional arguments:
  file                  path to input to serialise

options:
  -h, --help            show this help message and exit
  -j, --json            input as JSON
  -o OUTPUT, --output OUTPUT
                        path to the output file (default: original filename with cx extension)
  -H HEADER_TEXT, --header-text HEADER_TEXT
                        header text to use (only supported with XML, default: '')
  --original-path ORIGINAL_PATH
                        override original path to use in the header (only supported with XML, default: passed path to input)
  --build-number BUILD_NUMBER
                        build number to use in the header (only supported with XML, default: 123)
  --cx-version CX_VERSION
                        cx version to use in the header (only supported with XML, default: 3)
```

## `tearipper.py`

```plaintext
usage: tearipper.py [-h] {dump,decode,package,init,unpackage,play} ...

Extract, decode, dump, and package modified files for Tea for God modding.

positional arguments:
  {dump,decode,package,init,unpackage,play}
    dump                dump all encoded files from a game directory recursively
    decode              decode a single file
    package             package a dumped directory into a mod file
    init                initialize a mod configuration file (interactive, cannot be used automatically!)
    unpackage           unpackage a mod file into a directory
    play                launch the game with mods active

options:
  -h, --help            show this help message and exit

usage: tearipper.py dump [-h] [--output OUTPUT] [--overwrite] [-s] [--reg-path REG_PATH] [-j] [-m] directory

positional arguments:
  directory            directory to dump files from

options:
  -h, --help           show this help message and exit
  --output OUTPUT      output directory to dump files to (default: passed directory, same folders and structure as input files)
  --overwrite          overwrite existing files in output directory
  -s, --skip-existing  skip existing files in output directory
  --reg-path REG_PATH  path to save teareg registry file for later packaging (default: passed directory/dump.teareg)
  -j, --use-json       use json for cx deserialization for better accuracy (default: xml)
  -m, --mod            create configuration files for a mod (default: none created, you can create them manually later with the init command)

usage: tearipper.py decode [-h] [-j] file

positional arguments:
  file            file to decode

options:
  -h, --help      show this help message and exit
  -j, --use-json  use json for cx deserialization for better accuracy (default: xml)

usage: tearipper.py package [-h] [--reg-path REG_PATH] [--config CONFIG] [--output OUTPUT] [--pause-before-zip] directory

positional arguments:
  directory            directory to package

options:
  -h, --help           show this help message and exit
  --reg-path REG_PATH  path to teareg registry file to use for packaging (default: passed directory/dump.teareg)
  --config CONFIG      configuration file to use for packaging (default: passed directory/<config name>.mod.json)
  --output OUTPUT      output file to package to (default: <config name>.teamod)
  --pause-before-zip   pause before zipping to allow for manual file changes

usage: tearipper.py init [-h] directory

positional arguments:
  directory   directory to initialize configuration file in

options:
  -h, --help  show this help message and exit

usage: tearipper.py unpackage [-h] file output

positional arguments:
  file        file to unpackage
  output      output directory to unpackage to

options:
  -h, --help  show this help message and exit

usage: tearipper.py play [-h] directory mods

positional arguments:
  directory   path to game files
  mods        path to directory containing mods to load

options:
  -h, --help  show this help message and exit
```
