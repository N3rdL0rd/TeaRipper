formats = {
    'ogg': {
        'headera': [b'OggS'],
        'extension': '.ogg',
        'read_from': 'start',
        'read_until': 128
    },
    'mp3': {
        'headers': [b'ID3'],
        'extension': '.mp3',
        'read_from': 'start',
        'read_until': 128
    },
    'wav': {
        'headers': [b'RIFF', b'Info'],
        'extension': '.wav',
        'read_from': 'start',
        'read_until': 128
    }
}

def do_snd(data: bytes):
    out = None
    for format in formats:
        for header in formats[format]['headers']:
            loc = data.find(header)
            if loc != -1 and loc < formats[format]['read_until']:
                out = data[loc:]
                break
    return out