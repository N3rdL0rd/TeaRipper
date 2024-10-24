import colorama
import os
import json
import shutil
import hashlib
from teacx import format_leading_to_gamedir, xml_to_cx, json_to_cx
from typing import Tuple
import subprocess

def hash(file):
    try:
        h = hashlib.sha256()
        with open(file, 'rb') as file:
            chunk = 0
            while chunk != b'':
                chunk = file.read(1024)
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None

def err(msg):
    print(colorama.Fore.RED + msg + colorama.Style.RESET_ALL)

def warn(msg):
    print(colorama.Fore.YELLOW + msg + colorama.Style.RESET_ALL)

def init(dir):
    print(f'Initializing mod configuration in {dir}')
    mod_config = {
        "id": input('Mod ID (all lowercase, no spaces): '),
        "name": input('Mod name: '),
        "author": input('Author: '),
        "description": input('Description: '),
        "version": 0
    }
    with open(os.path.join(dir, mod_config['id'] + '.mod.json'), 'w') as f:
        json.dump(mod_config, f)

def package(directory: str, reg_path=None, config_path=None, output_path=None, pause_before_zip=False):
    print(f'Packaging {directory}...')
    testbuild = False
    if os.path.exists(os.path.join(directory, '_devConfig.xml')):
        print("This appears to be a test build. CX reserialisation will be skipped.")
        testbuild = True
    if not testbuild:
        print("Reserialising CX files...")
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.cx'):
                    print(f'Reserialising {root}/{file}')
                    for file2 in files:
                        if file2 == file.replace('.cx', '.xml'):
                            cxfile = xml_to_cx(os.path.join(root, file2))
                            break
                        if file2 == file.replace('.cx', '.json'):
                            cxfile = json_to_cx(os.path.join(root, file2))
                            break
                    try:
                        cxfile
                    except NameError:
                        warn(f'Warning: {root}/{file} has no corresponding .xml or .json file')
                        continue
                    with open(os.path.join(root, file), 'wb') as f:
                        f.write(cxfile.serialise())
    warn("WARNING: You should reserialise all files other than .cx files before packaging by hand. This tool will not do it for you.\n\
          For instance - all .wav files should be reserialised to .snd files, or should be placed in the _source folder for the game to correctly load them.")
    print("Cleaning up...")
    shutil.rmtree('temp', ignore_errors=True)
    new_reg = {}
    deleted = []
    new = []
    modified = []
    if reg_path is None:
        reg_path = os.path.join(directory, 'dump.teareg')
    old_reg = json.load(open(reg_path))
    if config_path is None:
        config_path = [f for f in os.listdir(directory) if f.endswith('.mod.json')]
        if len(config_path) == 0:
            err('Error: no configuration file found')
            return
        if len(config_path) > 1:
            err('Error: multiple configuration files found')
            return
        config_path = os.path.join(directory, config_path[0])
    config = json.load(open(config_path))
    for root, dirs, files in os.walk(directory):
        for file in files:
            print(f'Processing {root}/{file}')
            file = os.path.join(root, file)
            if file.startswith('/') or file.startswith('\\'):
                file = file[1:]
            if format_leading_to_gamedir(file) in old_reg:
                if old_reg[format_leading_to_gamedir(file)] != hash(file):
                    modified.append(format_leading_to_gamedir(file))
            else:
                new.append(format_leading_to_gamedir(file))
            new_reg[file] = hash(file)
    final_reg = {}
    ignored = ["/dump.teareg", "/packed.teareg"]
    for file in old_reg:
        if file in new or file in modified and file not in ignored and not "mod.json" in file:
            final_reg[file] = old_reg[file]
    for file in (new + modified):
        if file in ignored:
            continue
        real_file = os.path.join(directory, file[1:] if file.startswith('/') else file)
        final_reg[file] = hash(real_file)
    with open("packed.teareg", 'w') as f:
        json.dump(final_reg, f)
    if output_path is None:
        output_path = config['id'] + '.teamod'
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    print("Copying files...")
    for file in new + modified:
        orig_file = file
        if file.startswith('/') or file.startswith('\\'):
            file = file[1:]
        if "dump.teareg" in file or "mod.json" in file: # why is this necessary?
            continue
        if orig_file not in new_reg:
            new_reg[orig_file] = hash(os.path.join(directory, file))
        real_file = os.path.join(directory, file)
        print(f'Copying {real_file} to {temp_dir}')
        os.makedirs(os.path.join(temp_dir, os.path.dirname(file)), exist_ok=True)
        shutil.copy(real_file, os.path.join(temp_dir, file))
    print("Copying mod metadata...")
    shutil.copy("packed.teareg", os.path.join(temp_dir, "packed.teareg"))
    shutil.copy(config_path, os.path.join(temp_dir, "mod.json"))
    if pause_before_zip:
        input("       --- Paused ---\nInspect and modify files now, then press Enter to continue...")
    print("Creating archive...")
    shutil.make_archive(output_path, 'zip', temp_dir)
    shutil.rmtree(temp_dir)
    os.remove("packed.teareg")
    shutil.rmtree('temp', ignore_errors=True)
    shutil.move(output_path + '.zip', output_path) # shutil adds an extra .zip extension
    print(f'{colorama.Fore.BLUE}Packaged to {output_path}!{colorama.Style.RESET_ALL}')

danger_exts = ["dll", "exe", "bat"]

def unpackage(input_dir: str, output: str, show_virus_warning: bool=True, interactive_warning: bool=False, temp_dir: str="temp", backup_dir: str="backup") -> Tuple[dict, dict]:
    print(f"Unpackaging {input_dir}...")
    print("Cleaning up...")
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(output, exist_ok=True)
    shutil.unpack_archive(input_dir, temp_dir, format='zip')
    reg = json.load(open('temp/packed.teareg'))
    config = json.load(open('temp/mod.json'))
    for file in reg:
        orig_file = file
        if file.startswith('/') or file.startswith('\\'):
            file = file[1:]
        for ext in danger_exts:
            if file.lower().endswith(ext):
                if show_virus_warning:
                    warn(f'Warning: {file} is a potentially dangerous file type')
                if interactive_warning:
                    if input('Do you want to continue? (Y/n) ').lower() == 'n':
                        return
                    warn("Continuing, but be careful! Future warnings disabled.")
                    interactive_warning = False
        exist_path = os.path.join(output, file)
        if hash(exist_path) == hash(os.path.join(temp_dir, file)):
            print(f'{file} already exists and hashes match, skipping')
            continue
        if os.path.exists(exist_path):
            print(f'Backing up {file} to {os.path.join(backup_dir, file)}')
            os.makedirs(os.path.join(backup_dir, os.path.dirname(file)), exist_ok=True)
            shutil.copy(os.path.join(output, file), os.path.join(backup_dir, file))
        print(f'Copying {file} to {os.path.join(output, file)}')
        os.makedirs(os.path.join(output, os.path.dirname(file)), exist_ok=True)
        shutil.copy(os.path.join(temp_dir, file), os.path.join(output, file))
    print("Cleaning up...")
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f'{colorama.Fore.BLUE}Unpackaged to {output}!{colorama.Style.RESET_ALL}')
    return config, reg

def revert_from_backup(backup_dir: str, output: str):
    print(f"Reverting from backup {backup_dir} to {output}...")
    for root, dirs, files in os.walk(backup_dir):
        for file in files:
            backup_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(backup_file_path, backup_dir)
            output_file_path = os.path.join(output, relative_path)
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            shutil.copy(backup_file_path, output_file_path)
    print(f"{colorama.Fore.BLUE}Reverted {output}!{colorama.Style.RESET_ALL}")

def play(directory: str, mods: str):
    print(f'Loading mods...')
    backup_dir = 'backup'
    os.makedirs(backup_dir, exist_ok=True)
    for root, dirs, files in os.walk(mods):
        for file in files:
            if not file.endswith('.teamod'):
                continue
            mod_path = os.path.join(root, file)
            config, reg = unpackage(mod_path, directory, show_virus_warning=False, interactive_warning=False, backup_dir=backup_dir)
            print("Loaded mod: " + config['name'] + " by " + config['author'] + " v" + str(config['version']))
    print("Mods loaded!")
    print("Starting Tea for God...")
    old_dir = os.getcwd()
    os.chdir(directory)
    print(f"Currently in {os.getcwd()}")
    if os.path.exists("tfg.exe"):
        subprocess.run("tfg.exe", stdout=subprocess.STDOUT)
    elif os.path.exists("tea.exe"):
        subprocess.run("tea.exe", stdout=subprocess.STDOUT)
    else:
        print("Couldn't find main executable!")
    os.chdir(old_dir)
    print("Reverting from backup...")
    revert_from_backup(backup_dir, directory)
    shutil.rmtree(backup_dir)
