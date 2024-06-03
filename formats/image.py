def check_image(file_path: str) -> bool:
    with open(file_path, 'rb') as f:
        f.seek(0)
        if f.read(2) == b'BM':
            return True
        f.seek(-18, os.SEEK_END)
        if f.read() == b'TRUEVISION-XFILE.\x00' and not file.endswith('.tga'):
                print('TGA:', filepath)
                shutil.copyfile(filepath, filepath + '.tga')
                return