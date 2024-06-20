from common import *

class SndSerialisable(Serialisable):
    def __init__(self):
        raise NotImplementedError("SndSerialisable is an abstract class and should not be instantiated.")
    
    def deserialise(self, f) -> 'SndSerialisable':
        raise NotImplementedError("deserialise is not implemented for this class.")

class SndFile(SndSerialisable, SerialisableFile):
    