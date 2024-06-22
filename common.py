import struct
from typing import Dict

class Serialisable:
    def __init__(self):
        raise NotImplementedError("Serialisable is an abstract class and should not be instantiated.")

    def deserialise(self, f) -> 'Serialisable':
        raise NotImplementedError("deserialise is not implemented for this class.")
    
    def serialise(self) -> bytes:
        raise NotImplementedError("serialise is not implemented for this class.")
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __repr__(self) -> str:
        return str(self.value)
    
    def __eq__(self, other) -> bool:
        return self.value == other.value
    
    def __ne__(self, other) -> bool:
        return self.value != other.value
    
    def __lt__(self, other) -> bool:
        return self.value < other.value

class RawData(Serialisable):
    def __init__(self, length):
        self.data = b""
        self.length = length
    
    def deserialise(self, f) -> 'RawData':
        self.data = f.read(self.length)
        return self
    
    def serialise(self) -> bytes:
        return self.data
    
class SerialisableResourceHeader(Serialisable):
    # this class exists primarily for the sake of preserving the structure of the file - even with the digest being implemented, it's still mostly a black box
    def __init__(self):
        self.digested_source = RawData(16)
        self.digested_definition = RawData(16)
    
    def deserialise(self, f) -> 'SerialisableResourceHeader':
        self.digested_source.deserialise(f)
        self.digested_definition.deserialise(f)
        return self

    def serialise(self) -> bytes:
        return b"".join([self.digested_source.serialise(), self.digested_definition.serialise()])
    
    def digest(self, string: str, length: int=16) -> bytes:
        c_length = length
        value = [0] * c_length
        index = 0
        read_already = 0
        prev = 13
        for one in string.encode():
            if read_already < c_length:
                value[index] = (value[index] + (one - 83) + (prev & read_already)) % 256
            prev = one
            one += 26
            index = (index + 1) % c_length
            read_already += 1
        return bytes(value)
    
    def as_dict(self) -> Dict[str, str]:
        return {
            "digested_source": self.digested_source.data.hex(),
            "digested_definition": self.digested_definition.data.hex()
        }

    def generate_from(self, data: str) -> 'SerialisableResourceHeader':
        self.digested_source.data = self.digest(data)
        self.digested_definition.data = b"\x00" * 16 # TODO: figure out how to generate this. for now, 0x00 it is.
        return self
    
    def __str__(self) -> str:
        return f"SerialisableResourceHeader(digested_source={self.digested_source.data}, digested_definition={self.digested_definition.data})"
    
class SerialisableFile(Serialisable):
    def __init__(self):
        self.header = SerialisableResourceHeader()
        self.data = b""
    
    def deserialise(self, f) -> 'SerialisableFile':
        self.header.deserialise(f)
        self.data = f.read()
        return self

    def serialise(self) -> bytes:
        return b"".join([self.header.serialise(), self.data])
    
class SerialisableInt(Serialisable):
    def __init__(self):
        self.value = -1
        self.length = 4
        self.byteorder = "little"
        self.signed = False
    
    def deserialise(self, f, length=4, byteorder="little", signed=False) -> 'SerialisableInt':
        self.length = length
        self.byteorder = byteorder
        self.signed = signed
        bytes = f.read(length)
        if all(b == 0 for b in bytes):
            self.value = 0
            return self
        while bytes[-1] == 0:
            bytes = bytes[:-1]
        self.value = int.from_bytes(bytes, byteorder, signed=signed)
        return self
    
    def serialise(self) -> bytes:
        return self.value.to_bytes(self.length, self.byteorder, signed=self.signed)

class SerialisableFloat32(Serialisable):
    def __init__(self):
        self._length_DO_NOT_CHANGE = 4
        self.sign_bit = None
        self.exponent_byte = None
        self.significand_bytes = None
        self.value = None
    
    def deserialise(self, f) -> 'SerialisableFloat32':
        bytes = f.read(self._length_DO_NOT_CHANGE)
        # if all(b == 0 for b in bytes):
        #     self.value = 0.0
        #     return self
        self.sign_bit = bytes[0] >> 7
        self.exponent_byte = bytes[0] & 0x7F
        self.significand_bytes = bytes[1:]
        self.value = struct.unpack("<f", bytes)[0]
        return self

class SerialisableBool(Serialisable):
    def __init__(self):
        self.value = False
        self.length = 1
        self.cxint = SerialisableInt()
        self.cxint.length = 1
        self.cxint.signed = False
    
    def deserialise(self, f, length=1) -> 'SerialisableBool':
        self.length = length
        self.cxint.deserialise(f, length=length, signed=False)
        self.value = self.cxint.value == 1
        return self
    
    def serialise(self) -> bytes:
        self.cxint.value = 1 if self.value else 0
        return self.cxint.serialise()

class SerialisableString(Serialisable):
    def __init__(self):
        self.value = ""
        self.is_8_bit = SerialisableBool()
        self.is_8_bit.value = True # default to 8-bit
        self.length = SerialisableInt()
    
    def deserialise(self, f) -> 'SerialisableString':
        self.is_8_bit.deserialise(f)
        self.length.deserialise(f)
        if self.length.value == 0:
            self.value = ""
            return self
        if self.is_8_bit.value:
            self.value = f.read(self.length.value).decode("utf-8")
        else:
            raise NotImplementedError("Unicode strings are not supported yet")
        return self

    def serialise(self) -> bytes:
        encoded = None
        if self.is_8_bit.value:
            encoded = self.value.encode("utf-8")
        else:
            raise NotImplementedError("Unicode strings are not supported yet")
        self.length.value = len(encoded)
        return b"".join([self.is_8_bit.serialise(), self.length.serialise(), encoded])