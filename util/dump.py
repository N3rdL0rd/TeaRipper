import colorama
import os
from typing import Tuple
import traceback
from teacx import read_cx, cx_to_xml, cx_to_json, format_leading_to_gamedir
import hashlib
import json
from util.mod import init

supported_formats = ['ogg', 'mp3', 'tga', 'bmp', 'wav', 'xml', 'cx']

def process_snd_file(f) -> Tuple[bytes, str]:
    # custom sound file format - it's actually an OGG but with a bunch of junk at the start
    data = data[data.find(b'OggS'):]
    if len(data) > 30:
        return data, 'ogg'
    # try looking for ID3 tags
    data = data[data.find(b'ID3'):]
    if len(data) > 30:
        return data, 'mp3'
    # jesus christ - wav??
    data = data[data.find(b'Info'):]
    if len(data) > 30:
        return data, 'wav'
    data = data[data.find(b'RIFF'):]
    if len(data) > 30:
        return data, 'wav'
    return None, None
    
def process_other_file(f, path, use_json=False) -> Tuple[bytes, str]:
    if path.endswith('.cx'):
        f.seek(0)
        file = read_cx(f)
        if not use_json:
            return cx_to_xml(file).encode('utf-8'), 'xml'
        else:
            return cx_to_json(file).encode('utf-8'), 'json'
    if os.path.getsize(path) >= 18:
        f.seek(-18, os.SEEK_END)
        if f.read() == b'TRUEVISION-XFILE.\x00' and not path.endswith('.tga'):
            f.seek(0)
            data = f.read()
            return data, 'tga'
    f.seek(0)
    if f.read(2) == b'BM' and not path.endswith('.bmp'):
        f.seek(0)
        data = f.read()
        return data, 'bmp'

def err(msg):
    print(colorama.Fore.RED + msg + colorama.Style.RESET_ALL)

def warn(msg):
    print(colorama.Fore.YELLOW + msg + colorama.Style.RESET_ALL)

def process_file(root, file, log_failed=False, use_json=False) -> Tuple[bytes, str]:
    try:
        if file.split('.')[-1] in supported_formats:
            return None, None
        filepath = os.path.join(root, file)
        filepath_noext = os.path.splitext(filepath)[0]
        if filepath.endswith('.snd'):
            with open(filepath, 'rb') as f:
                data, ext = process_snd_file(f)
                if data is not None:
                    return data, filepath_noext + '.' + ext
                else:
                    warn(f'{filepath}: could not process sound file')
                    return None, None
        with open(filepath, 'rb') as f:
            data, ext = process_other_file(f, filepath, use_json=use_json)
            if data is not None:
                return data, filepath_noext + '.' + ext
            else:
                warn(f'{filepath}: could not process file')
                return None, None
    except Exception as e:
        if log_failed:
            err(f'Error processing {filepath}: {e}')
            traceback.print_exc()
        return None, None

def hash(file):
    h = hashlib.sha256()
    with open(file, 'rb') as file:
        chunk = 0
        while chunk != b'':
            chunk = file.read(1024)
            h.update(chunk)
    return h.hexdigest()

def dump(dir, output=None, overwrite=False, skip_existing=False, reg_path=None, mod=False, use_json=False):
    if not os.path.isdir(dir):
        err(f'Error: {dir} is not a directory')
        return
    testbuild = False
    if os.path.exists(os.path.join(dir, '_devConfig.xml')):
        print("This appears to be a test build. CX decoding will be skipped.")
        testbuild = True
    print(f'Dumping {dir}')
    reg = {}
    for root, dirs, files in os.walk(dir):
        for file in files:
            print(f'Processing {file}')
            reg[format_leading_to_gamedir(os.path.join(root, file))] = hash(os.path.join(root, file))
            data, newpath = process_file(root, file, use_json=use_json)
            if data is None:
                continue
            if output is None:
                output = dir
            if not os.path.isdir(output):
                os.makedirs(output)
            newpath = os.path.join(output, newpath)
            if os.path.exists(newpath) and not overwrite:
                if skip_existing or testbuild:
                    continue
                err(f'Error: {newpath} already exists')
                exit(1)
            with open(newpath, 'wb') as f:
                f.write(data)
    if reg_path is None:
        reg_path = os.path.join(dir, 'dump.teareg')
    with open(reg_path, 'w') as f:
        json.dump(reg, f)
    if mod:
        init(dir)
    print(colorama.Fore.BLUE + 'Done!' + colorama.Style.RESET_ALL)

def decode(file, use_json=False):
    if not os.path.isfile(file):
        err(f'Error: {file} is not a file')
        return
    print(f'Decoding {file}')
    with open(file, 'rb') as f:
        data, newpath = process_file(os.path.dirname(file), os.path.basename(file), log_failed=True, use_json=use_json)
        if data is None:
            return
        with open(newpath, 'wb') as f2:
            f2.write(data)