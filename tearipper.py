import os
import shutil
import argparse
from teacx import parse_cx, cx_to_xml
from formats.snd import do_snd
from formats.image import do_img, check_image

format_processors = {
    'snd': {
        'processor': do_snd,
        'match': lambda file: file.endswith('.snd'),
        'outputs': ['ogg', 'mp3', 'wav'],
        'returns': 'bytes'
    },
    'cx': {
        'processor': lambda data: cx_to_xml(parse_cx(data)),
        'match': lambda file: file.endswith('.cx'),
        'outputs': ['xml'],
        'returns': 'str'
    },
    'image': {
        'processor': do_img,
        'match': check_image,
        'outputs': ['tga', 'bmp'],
        'returns': 'bytes'
    }
}
supported_formats = set(ext for processor in format_processors.values() for ext in processor['outputs'])

def process_file(root, file, do_cx=False, log_failed=False):
    if file.split('.')[-1] in supported_formats:
        return

    filepath = os.path.join(root, file)
    with open(filepath, 'rb') as f:
        data = f.read()

    for format, processor in format_processors.items():
        if processor['match'](file):
            output, new_file = processor['processor'](data)
            if output:
                with open(new_file, 'wb') as f2:
                    f2.write(output)
            return

    if log_failed:
        print('Error: Unknown format for:', filepath)

def crawl_directory(path, do_cx=False):
    for root, dirs, files in os.walk(path):
        for file in files:
            process_file(root, file, do_cx)

def dump(directory):
    if not os.path.isdir(directory):
        print(f'Error: {directory} is not a directory')
        return
    print(f'Dumping {directory}')
    crawl_directory(directory)

def decode(file):
    if not os.path.isfile(file):
        print(f'Error: {file} is not a file')
        return
    process_file(os.path.dirname(file), os.path.basename(file), True, True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract and convert assets from Tea for God')
    subparsers = parser.add_subparsers(dest='action', required=True)

    dump_parser = subparsers.add_parser('dump', help='Decode all supported files in a game directory recursively')
    dump_parser.add_argument('directory', type=str, help='Directory to dump')
    dump_parser.set_defaults(func=dump)

    decode_parser = subparsers.add_parser('decode', help='Decode a single file')
    decode_parser.add_argument('file', type=str, help='File to decode')
    decode_parser.set_defaults(func=decode)

    args = parser.parse_args()
    if args.action == 'dump':
        dump(args.directory)
    elif args.action == 'decode':
        decode(args.file)
    else:
        parser.print_help()