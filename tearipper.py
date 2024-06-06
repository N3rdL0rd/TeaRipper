import argparse
from util.dump import dump, decode
from util.mod import package, init, unpackage, play

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract, decode, dump, and package modified files for Tea for God modding.')
    subparsers = parser.add_subparsers(dest='action', required=True)

    dump_parser = subparsers.add_parser('dump', help='dump all encoded files from a game directory recursively')
    dump_parser.add_argument('directory', help='directory to dump files from')
    dump_parser.add_argument('--output', help='output directory to dump files to (default: passed directory, same folders and structure as input files)')
    dump_parser.add_argument('--overwrite', action='store_true', help='overwrite existing files in output directory')
    dump_parser.add_argument('-s', '--skip-existing', action='store_true', help='skip existing files in output directory')
    dump_parser.add_argument('--reg-path', help='path to save teareg registry file for later packaging (default: passed directory/dump.teareg)')
    dump_parser.add_argument('-j', '--use-json', action='store_true', help='use json for cx deserialization for better accuracy (default: xml)')
    dump_parser.add_argument('-m', '--mod', action='store_true', help='create configuration files for a mod (default: none created, you can create them manually later with the init command)')    

    decode_parser = subparsers.add_parser('decode', help='decode a single file')
    decode_parser.add_argument('file', help='file to decode')
    decode_parser.add_argument('-j', '--use-json', action='store_true', help='use json for cx deserialization for better accuracy (default: xml)')

    package_parser = subparsers.add_parser('package', help='package a dumped directory into a mod file')
    package_parser.add_argument('directory', help='directory to package')
    package_parser.add_argument('--reg-path', help='path to teareg registry file to use for packaging (default: passed directory/dump.teareg)')
    package_parser.add_argument('--config', help='configuration file to use for packaging (default: passed directory/<config name>.mod.json)')
    package_parser.add_argument('--output', help='output file to package to (default: <config name>.teamod)')
    package_parser.add_argument('--pause-before-zip', action='store_true', help='pause before zipping to allow for manual file changes')

    init_parser = subparsers.add_parser('init', help='initialize a mod configuration file (interactive, cannot be used automatically!)')
    init_parser.add_argument('directory', help='directory to initialize configuration file in')

    unpackage_parser = subparsers.add_parser('unpackage', help='unpackage a mod file into a directory')
    unpackage_parser.add_argument('file', help='file to unpackage')
    unpackage_parser.add_argument('output', help='output directory to unpackage to')

    play_parser = subparsers.add_parser('play', help='launch the game with mods active')
    play_parser.add_argument('directory', help='path to game files')
    play_parser.add_argument('mods', help='path to directory containing mods to load')

    args = parser.parse_args()

    if args.action == 'dump':
        dump(args.directory, args.output, args.overwrite, args.skip_existing, args.reg_path, args.mod, args.use_json)
    elif args.action == 'decode':
        decode(args.file, args.use_json)
    elif args.action == 'package':
        package(args.directory, args.reg_path, args.config, args.output, pause_before_zip=args.pause_before_zip)
    elif args.action == 'init':
        init(args.directory)
    elif args.action == 'unpackage':
        unpackage(args.file, args.output, interactive_warning=True)
    elif args.action == 'play':
        play(args.directory, args.mods)
    else:
        parser.print_help()
        exit(1)