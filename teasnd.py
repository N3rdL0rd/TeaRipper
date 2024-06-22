from common import *
from typing import Dict, Any, Tuple
from pprint import pprint

class SoundData(RawData):
    def __init__(self, length):
        super().__init__(length)
        self.format = "UNKNOWN!"
    
    def deserialise(self, f) -> 'SoundData':
        self.data = f.read(self.length)
        if data.startswith(b'OggS'):
            self.format = "OGG"
        elif data.startswith(b'ID3'):
            self.format = "MP3"
        elif data.startswith(b'Info') or data.startswith(b'RIFF'):
            self.format = "WAV"
        return self

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
            "looped": self.looped.value,
            "is3D": self.is3D.value,
            "channel_name": self.channel_name.value,
            "hearing_distance": self.hearing_distance.as_dict(),
            "volume": self.volume.as_dict(),
            "pitch": self.pitch.as_dict(),
            "sound_priority": self.sound_priority.value,
            "doppler_level": self.doppler_level.value
        }

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
        return f"""snd file v{self.version.value}
{str(self.resourceheader)}
{str(self.sampleparams)}
data length: {self.data_length.value}"""

if __name__ == "__main__":
    with open("../latest/system/music/assets/loading.snd", "rb") as f:
        file = SndFile().deserialise(f)
        meta, data = file.as_dict_and_data()
        pprint(meta)