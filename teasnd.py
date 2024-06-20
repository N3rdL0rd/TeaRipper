from common import *

class SndSerialisable(Serialisable):
    def __init__(self):
        raise NotImplementedError("SndSerialisable is an abstract class and should not be instantiated.")
    
    def deserialise(self, f) -> 'SndSerialisable':
        raise NotImplementedError("deserialise is not implemented for this class.")

class SampleParams(SndSerialisable):
    def __init__(self):
        self.version = SerialisableInt()
        

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