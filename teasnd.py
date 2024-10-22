from common import *
from typing import Dict, Any, Tuple
import json
import argparse
import os

class SoundData(RawData):
    def __init__(self, length):
        super().__init__(length)
        self.format = "UNKNOWN!"
    
    def deserialise(self, f) -> 'SoundData':
        self.data = f.read(self.length)
        if self.data.startswith(b'OggS'):
            self.format = "OGG"
        elif self.data.startswith(b'ID3'):
            self.format = "MP3"
        elif self.data.startswith(b'Info') or data.startswith(b'RIFF'):
            self.format = "WAV"
        else:
            print("Unknown sound format!")
            self.format = "UNKNOWN!"
        return self
    
    def __str__(self) -> str:
        return f"SoundData({self.format})"

class SndSerialisable(Serialisable):
    def __init__(self):
        raise NotImplementedError("SndSerialisable is an abstract class and should not be instantiated.")
    
    def deserialise(self, f) -> 'SndSerialisable':
        raise NotImplementedError("deserialise is not implemented for this class.")

class SerialisableRange(SndSerialisable):
    def __init__(self):
        self.min = SerialisableFloat32()
        self.max = SerialisableFloat32()

    def deserialise(self, f) -> 'SerialisableRange':
        self.min.deserialise(f)
        self.max.deserialise(f)
        return self
    
    def as_dict(self) -> Dict[str, Any]:
        return {
            "min": self.min.value,
            "max": self.max.value
        }

    def serialise(self) -> bytes:
        return b"".join([self.min.serialise(), self.max.serialise()])

class SampleParams(SndSerialisable):
    def __init__(self):
        self.version = SerialisableInt()
        self.looped = SerialisableBool()
        self.is3D = SerialisableBool()
        self.channel_name = SerialisableString()
        self.hearing_distance = SerialisableRange()
        self.volume = SerialisableRange()
        self.pitch = SerialisableRange()
        self.sound_priority = SerialisableInt()
        self.doppler_level = SerialisableFloat32()

    def deserialise(self, f) -> 'SampleParams':
        self.version.deserialise(f)
        self.looped.deserialise(f)
        self.is3D.deserialise(f)
        self.channel_name.deserialise(f)
        self.hearing_distance.deserialise(f)
        self.volume.deserialise(f)
        self.pitch.deserialise(f)
        self.sound_priority.deserialise(f)
        self.doppler_level.deserialise(f)
        return self

    def serialise(self) -> bytes:
        return b"".join([
            self.version.serialise(),
            self.looped.serialise(),
            self.is3D.serialise(),
            self.channel_name.serialise(),
            self.hearing_distance.serialise(),
            self.volume.serialise(),
            self.pitch.serialise(),
            self.sound_priority.serialise(),
            self.doppler_level.serialise()
        ])
    
    def as_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version.value,
            "looped": self.looped.value,
            "is3D": self.is3D.value,
            "channel_name": self.channel_name.value,
            "hearing_distance": self.hearing_distance.as_dict(),
            "volume": self.volume.as_dict(),
            "pitch": self.pitch.as_dict(),
            "sound_priority": self.sound_priority.value,
            "doppler_level": self.doppler_level.value
        }
    
    def from_dict(self, data: Dict[str, Any]) -> 'SampleParams':
        self.version.value = data["version"]
        self.looped.value = data["looped"]
        self.is3D.value = data["is3D"]
        self.channel_name.value = data["channel_name"]
        self.hearing_distance.min.value = data["hearing_distance"]["min"]
        self.hearing_distance.max.value = data["hearing_distance"]["max"]
        self.volume.min.value = data["volume"]["min"]
        self.volume.max.value = data["volume"]["max"]
        self.pitch.min.value = data["pitch"]["min"]
        self.pitch.max.value = data["pitch"]["max"]
        self.sound_priority.value = data["sound_priority"]
        self.doppler_level.value = data["doppler_level"]
        return self

    def __str__(self) -> str:
        return f"SampleParams(looped={self.looped.value}, is3D={self.is3D.value}, channel_name={self.channel_name.value}, hearing_distance={self.hearing_distance.min.value}-{self.hearing_distance.max.value}, volume={self.volume.min.value}-{self.volume.max.value}, pitch={self.pitch.min.value}-{self.pitch.max.value}, sound_priority={self.sound_priority.value}, doppler_level={self.doppler_level.value})"

class SndFile(SndSerialisable, SerialisableFile):
    def __init__(self):
        self.version = SerialisableInt()
        self.resourceheader = SerialisableResourceHeader()
        self.sampleparams = SampleParams()
        self.data_length = SerialisableInt()
        self.data = SoundData(0)

    def deserialise(self, f) -> 'SndFile':
        self.version.deserialise(f, length=2)
        self.resourceheader.deserialise(f)
        self.sampleparams.deserialise(f)
        self.data_length.deserialise(f)
        self.data = SoundData(self.data_length.value)
        self.data.deserialise(f)
        return self
    
    def serialise(self) -> bytes:
        self.version.length = 2
        return b"".join([
            self.version.serialise(),
            self.resourceheader.serialise(),
            self.sampleparams.serialise(),
            self.data_length.serialise(),
            self.data.serialise()
        ])
    
    def as_dict_and_data(self) -> Tuple[Dict[str, Any], bytes]:
        return {
            "format": self.data.format,
            "version": self.version.value,
            "resourceheader": self.resourceheader.as_dict(),
            "sampleparams": self.sampleparams.as_dict(),
            "data_length": self.data_length.value
        }, self.data.data
    
    def from_dict_and_data(self, data: Dict[str, Any], data_bytes: bytes) -> 'SndFile':
        self.version.value = data["version"]
        self.resourceheader.from_dict(data["resourceheader"])
        self.sampleparams.from_dict(data["sampleparams"])
        self.data_length.value = data["data_length"]
        self.data.data = data_bytes
        return self
    
    def __str__(self):
        return f"""----- SND file v{self.version.value} -----
 - Header - 
{str(self.resourceheader)}
{str(self.sampleparams)}
 - Data - 
Data length: {self.data_length.value}
Format: {str(self.data)}"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deserialise, serialise, and display information about a .snd file')
    subparsers = parser.add_subparsers(dest='action', required=True)

    deserialise_parser = subparsers.add_parser('deserialise', help='deserialise a .snd file')
    deserialise_parser.add_argument('file', type=str, help='file to deserialise')
    deserialise_parser.add_argument('-o', '--output', type=str, help='output file to write deserialised data to (default: original file name with auto-detected extension)')
    deserialise_parser.add_argument('-f', '--format', type=str, help='snd data format (default: auto-detected, can be OGG, MP3, or WAV)')
    deserialise_parser.add_argument('-j', '--json-path', type=str, help='path to a JSON file to write the header information to (default: original file name with .json extension)')
    deserialise_parser.add_argument('--just-data', action='store_true', help='only output the sound data - makes it impossible to reserialise identically')

    serialise_parser = subparsers.add_parser('serialise', help='serialise a .snd file')
    serialise_parser.add_argument('file', type=str, help='file to serialise')
    serialise_parser.add_argument('-o', '--output', type=str, help='output file to write serialised data to (default: original file name with .snd extension)')
    serialise_parser.add_argument('-j', '--json-path', type=str, help='path to a JSON file containing the header information (default: original file name with .json extension)')

    info_parser = subparsers.add_parser('info', help='display information about a .snd file')
    info_parser.add_argument('file', type=str, help='file to display information about')

    args = parser.parse_args()

    if args.action == 'deserialise':
        if not args.file.endswith('.snd'):
            print("That doesn't look like a .snd file!")
            exit(1)
        json_output = args.json_path if args.json_path else args.file.replace('.snd', '.json')
        file = SndFile().deserialise(open(args.file, 'rb'))
        header, data = file.as_dict_and_data()
        print(str(file))
        if args.format:
            file.data.format = args.format
        if args.output:
            open(args.output, 'wb').write(data)
        else:
            open(args.file.replace('.snd', f'.{file.data.format.lower()}'), 'wb').write(data)
        if not args.just_data:
            with open(json_output, 'w') as f:
                f.write(json.dumps(header, indent=4))

    elif args.action == 'serialise':
        file_noext = os.path.splitext(args.file)[0]
        json_path = args.json_path if args.json_path else file_noext + '.json'
        header = json.load(open(json_path))
        data = open(args.file, 'rb').read()
        file = SndFile().from_dict_and_data(header, data)
        if args.output:
            open(args.output, 'wb').write(file.serialise())
        else:
            open(file_noext + '.snd', 'wb').write(file.serialise())
        
    elif args.action == 'info':
        if not args.file.endswith('.snd'):
            print("That doesn't look like a .snd file!")
        file = SndFile().deserialise(open(args.file, 'rb'))
        print(str(file))