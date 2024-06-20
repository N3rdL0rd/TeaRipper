from common import *

# snd file:
# 2 bytes     int     version     right now it is 0
# fixed       SerialisableResourceHeader
# fixed       SampleParams
# 4 bytes     int     length of sound data (sound file)
# variable            actual sound data of length of above

# SampleParams serialisation
# 4 bytes     int     version (sample params) right now it is 3
# 1 byte      bool    if sound is looped
# 1 byte      bool    if sound is 3D
#             Name    channel name
#             Range   distances for hearing
#             Range   volume
#             Range   pitch
# 4 bytes     int     sound priority
# 4 bytes     float   doppler level

# Name serialisation
# this is the same as string serialisation
# I used to have "name library" but in most of the cases it was only making it harder to read/write
# I added this info just as a precaution but in most cases Name should be considered String

# Range serialisation
# 4 bytes     float   min value
# 4 bytes     float   max value

class SndSerialisable(Serialisable):
    def __init__(self):
        raise NotImplementedError("SndSerialisable is an abstract class and should not be instantiated.")
    
    def deserialise(self, f) -> 'SndSerialisable':
        raise NotImplementedError("deserialise is not implemented for this class.")

class SerialisableRange(SndSerialisable):
    def __init__(self):
        self.min = SerialisableFloat()
        self.max = SerialisableFloat()

    def deserialise(self, f) -> 'SerialisableRange':
        self.min.deserialise(f)
        self.max.deserialise(f)
        return self

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
        self.doppler_level = SerialisableFloat() # TODO: floats!

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

class SndFile(SndSerialisable, SerialisableFile):
    def __init__(self):
        self.version = SerialisableInt()
        self.version.length = 2
        self.resourceheader = SerialisableResourceHeader()
        self.sampleparams = SampleParams()
        self.data_length = SerialisableInt()
        self.data = RawData(0)

    def deserialise(self, f) -> 'SndFile':
        self.version.deserialise(f)
        self.resourceheader.deserialise(f)
        self.sampleparams.deserialise(f)
        self.data_length.deserialise(f)
        self.data = RawData(self.data_length.value)
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