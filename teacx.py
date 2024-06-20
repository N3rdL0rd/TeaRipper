"""
Utility for Tea for God's custom encoding for XML files, .cx - version 2 (based on official docs)

Written by N3rdL0rd. This version is from 6/6/2024.

Thank you to void room for the official documentation and the huge help in understanding the format.
"""
import json
import argparse
import io
import os
from lxml import etree
from typing import List
from common import *

# region Classes
class CXSerialisable(Serialisable):
    def __init__(self):
        raise NotImplementedError("CXSerialisable is an abstract class and should not be instantiated.")
    
    def deserialise(self, f) -> 'CXSerialisable':
        raise NotImplementedError("deserialise is not implemented for this class.")

class CXAttribute(CXSerialisable):
    def __init__(self):
        self.name = SerialisableString()
        self.value = SerialisableString()
    
    def deserialise(self, f) -> 'CXAttribute':
        self.name.deserialise(f)
        self.value.deserialise(f)
        return self
    
    def serialise(self) -> bytes:
        return b"".join([self.name.serialise(), self.value.serialise()])

    def __repr__(self) -> str:
        return f"{self.name.value}={self.value.value}"
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __eq__(self, other) -> bool:
        return self.name == other.name and self.value == other.value
    
    def __ne__(self, other) -> bool:
        return not self == other
    
    def __lt__(self, other) -> bool:
        raise NotImplementedError("Comparison is not implemented for CXAttribute")

class CXNodeType(CXSerialisable):
    def __init__(self):
        self.human_readable = {
            0: "Node",
            1: "Text",
            2: "Comment",
            3: "Root (Virtual)",
            4: "Commented-out Node"
        }
        self.cxint = SerialisableInt()
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
        self.line_number = SerialisableInt()
        self.type = CXNodeType()
        self.content = SerialisableString()
        self.attribute_count = SerialisableInt()
        self.attributes = []
        self.child_count = SerialisableInt()
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
    

class CXHeader(CXSerialisable):
    def __init__(self):
        self.cx_version = SerialisableInt()
        self.cx_version.length = 2
        self.serialisable_resource_header = SerialisableResourceHeader()
        self.original_file_path = SerialisableString()
        self.build_number = SerialisableInt()
        self.header_text = SerialisableString()
    
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

class CXFile(CXSerialisable, SerialisableFile):
    def __init__(self):
        self.header = CXHeader()
        self.root_node = CXNode()
    
    def deserialise(self, f) -> 'CXFile':
        self.header.deserialise(f)
        self.root_node.deserialise(f)
        return self
    
    def serialise(self) -> bytes:
        return b"".join([self.header.serialise(), self.root_node.serialise()])

    def __repr__(self) -> str:
        return f"<CXFile {self.header.original_file_path.value}>"
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __eq__(self, other) -> bool:
        return self.header.serialisable_resource_header == other.header.serialisable_resource_header and self.root_node == other.root_node
    
    def __ne__(self, other) -> bool:
        return not self == other
    
    def __lt__(self, other) -> bool:
        raise NotImplementedError("Comparison is not implemented for CXFile")

# region Helpers
def read_cx(f) -> CXFile:
    return CXFile().deserialise(f)

def read_cx_path(file_path: str) -> CXFile:
    with open(file_path, "rb") as f:
        return read_cx(f)
    
def read_cx_bytes(data: bytes) -> CXFile:
    return read_cx(io.BytesIO(data))

# HACK: only way to get around lxml's inability to parse attributes with dots in the name
def encode_tagname(tagname: str) -> str:
    return tagname.replace(".", "thisisadotstupidxmlparser")

def decode_tagname(tagname: str) -> str:
    return tagname.replace("thisisadotstupidxmlparser", ".")

def replace_last(source_string: str, replace_what: str, replace_with: str) -> str:
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail

def strip_leading_to_gamedir(path: str) -> str:
    # game paths aren't always consistent, so we need to make sure the following is removed:
    # - leading dots and slashes
    # - leading "latest" or "latest/" (from my development environment, probably doesn't matter for anyone else, but it's just QoL)
    # - for compatibility's sake, also replace the last slash with a backslash (like what's generated from the game)    
    return replace_last(path.removeprefix("./").removeprefix("../").removeprefix("latest/").removeprefix("latest").replace("\\", "/"), "/", "\\")

def format_leading_to_gamedir(path: str) -> str:
    return path.removeprefix("./").removeprefix("../").removeprefix("latest/").removeprefix("latest").replace("\\", "/")

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

# region XML serialisation
def parse_attributes(node: etree.Element) -> List[CXAttribute]:
    res = []
    for k, v in node.items():
        cxattr = CXAttribute()
        cxattr.name.value = decode_tagname(k)
        cxattr.value.value = decode_tagname(v)
        res.append(cxattr)
    return res

def parse_node(node: etree.Element, type: str="Node") -> CXNode:
    cxnode = CXNode()
    cxnode.line_number.value = node.sourceline
    cxnode.type.value = type
    cxnode.content.value = decode_tagname(node.tag)
    cxnode.attributes = parse_attributes(node)
    cxnode.children = [parse_node(child) for child in node.iterchildren()]
    return cxnode

def parse_root_node(node: str) -> CXNode:
    # first, we need to find the attributes and replace dots in tag names
    node = encode_tagname(node)
    root = etree.fromstring(node)
    root_cx = CXNode()
    root_cx.line_number.value = 0
    root_cx.type.value = "Root (Virtual)"
    root_cx.content.value = ""
    root_cx.attributes = []
    root_cx.children = [parse_node(root)]
    return root_cx

def xml_to_cx(xml: str, original_path: str=None, header_text: str="", build_number: int=123, cx_version: int=3) -> CXFile:
    file = CXFile()
    file.header.build_number.value = build_number
    file.header.cx_version.value = cx_version
    file.header.original_file_path.value = original_path if original_path is not None else "unknown"
    file.header.header_text.value = header_text
    file.header.serialisable_resource_header.generate_from(xml)
    file.root_node = parse_root_node(xml)
    return file

# region Main
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse, serialise, and deserialise Tea for God .cx files")
    subparsers = parser.add_subparsers(dest="command", required=True)

    deserialise_parser = subparsers.add_parser('deserialise', help='Deserialise a cx file')
    deserialise_parser.add_argument("file", type=str, help="path to the .cx file")
    deserialise_parser.add_argument("-j", "--json", action="store_true", help="output as JSON")
    deserialise_parser.add_argument("-o", "--output", type=str, help="path to the output file (default: original filename with changed extension)")

    serialise_parser = subparsers.add_parser('serialise', help='Serialise a file to cx')
    serialise_parser.add_argument("file", type=str, help="path to input to serialise")
    serialise_parser.add_argument("-j", "--json", action="store_true", help="input as JSON")
    serialise_parser.add_argument("-o", "--output", type=str, help="path to the output file (default: original filename with cx extension)")
    serialise_parser.add_argument('-H', '--header-text', type=str, default="", help="header text to use (only supported with XML, default: '')")
    serialise_parser.add_argument("--original-path", type=str, help="override original path to use in the header (only supported with XML, default: passed path to input)")
    serialise_parser.add_argument("--build-number", type=int, default=123, help="build number to use in the header (only supported with XML, default: 123)")
    serialise_parser.add_argument("--cx-version", type=int, default=3, help="cx version to use in the header (only supported with XML, default: 3)")

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
            args.output = args.file[:args.file.find(".xml" if not args.json else ".json")] + ".cx.new"
        if args.original_path is None:
            args.original_path = args.file
        args.original_path = strip_leading_to_gamedir(args.original_path)
        if not args.json:
            with open(args.file, "r") as f:
                with open(args.output, "wb") as out:
                    out.write(xml_to_cx(f.read(), original_path=args.original_path, header_text=args.header_text, build_number=args.build_number, cx_version=args.cx_version).serialise())
        else:
            with open(args.file, "r") as f:
                with open(args.output, "wb") as out:
                    out.write(json_to_cx(json.load(f)).serialise())