"""
Utility for Tea for God's custom encoding for XML files, .cx - version 2 (based on official docs)

Written by N3rdL0rd. This is a work in progress and is not yet complete. This version is from 6/2/2024.

Thank you to void room for the official documentation and the huge help in understanding the format.
"""
import json
import argparse
import io
import os
import hashlib
import warnings

# region Classes
class CXSerialisable:
    def __init__(self):
        raise NotImplementedError("CXSerialisable is an abstract class and should not be instantiated.")
    
    def deserialise(self, f) -> 'CXSerialisable':
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

class CXInt(CXSerialisable):
    def __init__(self):
        self.value = -1
        self.length = 4
        self.byteorder = "little"
        self.signed = False
    
    def deserialise(self, f, length=4, byteorder="little", signed=False) -> 'CXInt':
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

class CXBool(CXSerialisable):
    def __init__(self):
        self.value = False
        self.length = 1
        self.cxint = CXInt()
        self.cxint.length = 1
        self.cxint.signed = False
    
    def deserialise(self, f, length=1) -> 'CXBool':
        self.length = length
        self.cxint.deserialise(f, length=length, signed=False)
        self.value = self.cxint.value == 1
        return self
    
    def serialise(self) -> bytes:
        self.cxint.value = 1 if self.value else 0
        return self.cxint.serialise()
    
class CXString(CXSerialisable):
    def __init__(self):
        self.value = ""
        self.is_8_bit = CXBool()
        self.is_8_bit.value = True # default to 8-bit
        self.length = CXInt()
    
    def deserialise(self, f) -> 'CXString':
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

class CXAttribute(CXSerialisable):
    def __init__(self):
        self.name = CXString()
        self.value = CXString()
    
    def deserialise(self, f) -> 'CXAttribute':
        self.name.deserialise(f)
        self.value.deserialise(f)
        return self
    
    def serialise(self) -> bytes:
        return b"".join([self.name.serialise(), self.value.serialise()])

class CXNodeType(CXSerialisable):
    def __init__(self):
        self.human_readable = {
            0: "Node",
            1: "Text",
            2: "Comment",
            3: "Root (Virtual)",
            4: "Commented-out Node"
        }
        self.cxint = CXInt()
        self.value = ""

    def deserialise(self, f) -> 'CXNodeType':
        self.cxint.deserialise(f)
        self.value = self.human_readable.get(self.cxint.value, "Unknown")
        return self
    
    def serialise(self) -> bytes:
        self.cxint.value = list(self.human_readable.keys())[list(self.human_readable.values()).index(self.value)]
        return self.cxint.serialise()

class CXNode(CXSerialisable):
    def __init__(self):
        self.line_number = CXInt()
        self.type = CXNodeType()
        self.content = CXString()
        self.attribute_count = CXInt()
        self.attributes = []
        self.child_count = CXInt()
        self.children = []
    
    def deserialise(self, f) -> 'CXNode':
        self.line_number.deserialise(f)
        self.type.deserialise(f)
        self.content.deserialise(f)

        self.attribute_count.deserialise(f)
        self.attributes = []
        for _ in range(self.attribute_count.value):
            self.attributes.append(CXAttribute().deserialise(f))

        self.child_count.deserialise(f)
        self.children = []
        for _ in range(self.child_count.value):
            self.children.append(CXNode().deserialise(f))
        return self

    def serialise(self) -> bytes:
        self.attribute_count.value = len(self.attributes)
        self.child_count.value = len(self.children)
        return b"".join([
            self.line_number.serialise(),
            self.type.serialise(),
            self.content.serialise(),
            self.attribute_count.serialise(),
            b"".join([attr.serialise() for attr in self.attributes]),
            self.child_count.serialise(),
            b"".join([child.serialise() for child in self.children])
        ])
    
    def __repr__(self) -> str:
        return f"<CXNode {self.content.value} {str(self.attributes)}>"

class CXRawData(CXSerialisable):
    def __init__(self, length):
        self.data = b""
        self.length = length
    
    def deserialise(self, f) -> 'CXRawData':
        self.data = f.read(self.length)
        return self
    
    def serialise(self) -> bytes:
        return self.data

class CXSerialisableResourceHeader(CXSerialisable):
    # this class exists primarily for the sake of preserving the structure of the file - but it does nothing until we can figure out how to parse this
    # the data is most likely an md5 hash of the xml source file, but the definition is usually 0x00 * 16, so it's not clear what it's for
    def __init__(self):
        self.digested_source = CXRawData(16)
        self.digested_definition = CXRawData(16)
    
    def deserialise(self, f) -> 'CXSerialisableResourceHeader':
        self.digested_source.deserialise(f)
        self.digested_definition.deserialise(f)
        return self

    def serialise(self) -> bytes:
        return b"".join([self.digested_source.serialise(), self.digested_definition.serialise()])
    
    def generate_from(self, file_path: str) -> 'CXSerialisableResourceHeader':
        warnings.warn("This function is not yet correctly implemented and *will* not work to generate matching headers.")
        with open(file_path, "rb") as f:
            data = f.read()
            digested_source = hashlib.md5(data).digest()
            self.digested_source.data = digested_source
            self.digested_definition.data = b"\x00" * 16
        return self

class CXHeader(CXSerialisable):
    def __init__(self):
        self.cx_version = CXInt()
        self.serialisable_resource_header = CXSerialisableResourceHeader()
        self.original_file_path = CXString()
        self.build_number = CXInt()
        self.header_text = CXString()
    
    def deserialise(self, f) -> 'CXHeader':
        self.cx_version.deserialise(f, length=2)
        self.serialisable_resource_header.deserialise(f)
        self.original_file_path.deserialise(f)
        self.build_number.deserialise(f)
        self.header_text.deserialise(f)
        return self
    
    def serialise(self) -> bytes:
        return b"".join([
            self.cx_version.serialise(),
            self.serialisable_resource_header.serialise(),
            self.original_file_path.serialise(),
            self.build_number.serialise(),
            self.header_text.serialise()
        ])

class CXFile(CXSerialisable):
    def __init__(self):
        self.header = CXHeader()
        self.root_node = CXNode()
    
    def deserialise(self, f) -> 'CXFile':
        self.header.deserialise(f)
        self.root_node.deserialise(f)
        return self
    
    def serialise(self) -> bytes:
        return b"".join([self.header.serialise(), self.root_node.serialise()])

# region Helpers
def read_cx(f) -> CXFile:
    return CXFile().deserialise(f)

def read_cx_path(file_path: str) -> CXFile:
    with open(file_path, "rb") as f:
        return read_cx(f)
    
def read_cx_bytes(data: bytes) -> CXFile:
    return read_cx(io.BytesIO(data))

# region JSON deserialisation
def attr_to_json(attr: CXAttribute) -> dict:
    return {
        "name": attr.name.value,
        "value": attr.value.value
    }

def node_to_json(node: CXNode) -> dict:
    return {
        "line_number": node.line_number.value,
        "type": node.type.value,
        "content": node.content.value,
        "attributes": [attr_to_json(attr) for attr in node.attributes],
        "children": [node_to_json(child) for child in node.children]
    }

def cx_to_json(file: CXFile) -> dict:
    return {
        "header": {
            "cx_version": file.header.cx_version.value,
            "serialisable_resource_header": {
                "digested_source": file.header.serialisable_resource_header.digested_source.data.hex(),
                "digested_definition": file.header.serialisable_resource_header.digested_definition.data.hex()
            },
            "original_file_path": file.header.original_file_path.value,
            "build_number": file.header.build_number.value,
            "header_text": file.header.header_text.value
        },
        "node": node_to_json(file.root_node)
    }

# region XML deserialisation
def node_to_xml(node: CXNode, indent: int = 0) -> str:
    indent_str = '    ' * indent
    if node.type.value == "Root (Virtual)":
        return "".join([node_to_xml(child, indent) for child in node.children])
    elif node.type.value == "Text":
        return indent_str + node.content.value
    elif node.type.value == "Comment":
        return f"{indent_str}<!-- {node.content.value} -->"
    elif node.type.value == "Node":
        attrs = " ".join([f'{attr.name.value}="{attr.value.value}"' for attr in node.attributes])
        if len(node.children) == 0:
            return f"{indent_str}<{node.content.value} {attrs} />"
        children = "".join([node_to_xml(child, indent + 2) for child in node.children])
        return f"{indent_str}<{node.content.value} {attrs}>\n{children}\n{indent_str}</{node.content.value}>"
    elif node.type.value == "Commented-out Node":
        attrs = " ".join([f'{attr.name.value}="{attr.value.value}"' for attr in node.attributes])
        if len(node.children) == 0:
            return f"{indent_str}<!-- <{node.content.value} {attrs} /> -->"
        children = "".join([node_to_xml(child, indent + 2) for child in node.children])
        return f"{indent_str}<!-- <{node.content.value} {attrs}>\n{children}\n{indent_str}</{node.content.value}> -->"
    else:
        raise ValueError("Unknown node type")

def cx_to_xml(file: CXFile) -> str:
    return "<!-- Decoded by TeaRipper v2 -->\n" + node_to_xml(file.root_node)

# region JSON serialisation
def json_to_attr(data: dict) -> CXAttribute:
    attr = CXAttribute()
    attr.name.value = data["name"]
    attr.value.value = data["value"]
    return attr

def json_to_node(data: dict) -> CXNode:
    node = CXNode()
    node.line_number.value = data["line_number"]
    node.type.value = data["type"]
    node.content.value = data["content"]
    node.attributes = [json_to_attr(attr) for attr in data["attributes"]]
    node.children = [json_to_node(child) for child in data["children"]]
    return node

def json_to_cx(data: dict) -> CXFile:
    file = CXFile()
    file.header.cx_version.value = data["header"]["cx_version"]
    file.header.cx_version.length = 2
    file.header.serialisable_resource_header.digested_source.data = bytes.fromhex(data["header"]["serialisable_resource_header"]["digested_source"])
    file.header.serialisable_resource_header.digested_definition.data = bytes.fromhex(data["header"]["serialisable_resource_header"]["digested_definition"])
    file.header.original_file_path.value = data["header"]["original_file_path"]
    file.header.build_number.value = data["header"]["build_number"]
    file.header.header_text.value = data["header"]["header_text"]
    file.root_node = json_to_node(data["node"])
    return file

# TODO: XML serialisation

# region Main
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse, serialise, and deserialise Tea for God .cx files")
    subparsers = parser.add_subparsers(dest="command")

    deserialise_parser = subparsers.add_parser('deserialise', help='Deserialise a cx file')
    deserialise_parser.add_argument("file", type=str, help="path to the .cx file")
    deserialise_parser.add_argument("-j", "--json", action="store_true", help="output as JSON")
    deserialise_parser.add_argument("-o", "--output", type=str, help="path to the output file (default: original filename with changed extension)")

    serialise_parser = subparsers.add_parser('serialise', help='Serialise a file to cx')
    serialise_parser.add_argument("file", type=str, help="path to input to serialise")
    serialise_parser.add_argument("-j", "--json", action="store_true", help="input as JSON")
    serialise_parser.add_argument("-o", "--output", type=str, help="path to the output file (default: original filename with cx extension)")
    serialise_parser.add_argument("--build-number", type=int, default=123, help="build number to use in the header (default: 123)")
    serialise_parser.add_argument("--cx-version", type=int, default=3, help="cx version to use in the header (default: 3)")

    args = parser.parse_args()

    if args.command == 'deserialise':
        if not os.path.exists(args.file):
            raise FileNotFoundError(f"File not found: {args.file}")    
        if args.output is None:
            args.output = args.file[:args.file.find(".cx")] + (".json" if args.json else ".xml")
        if not args.json:
            with open(args.output, "w") as f:
                f.write(cx_to_xml(read_cx_path(args.file)))
        else:
            with open(args.output, "w") as f:
                json.dump(cx_to_json(read_cx_path(args.file)), f, indent=4)
    elif args.command == 'serialise':
        if args.output is None:
            args.output = args.file[:args.file.find(".")] + ".cx"
        if not args.json:
            raise NotImplementedError("XML serialisation is not yet supported")
        else:
            with open(args.file, "r") as f:
                with open(args.output, "wb") as out:
                    out.write(json_to_cx(json.load(f)).serialise())