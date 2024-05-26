"""
Utility for Tea for God's custom encoding for XML files, .cx
"""
import string
import argparse
import json
from typing import Tuple

# region helpers
def remove_non_ascii(a_str: str) -> str:
    return (''.join([c if c in set(string.printable) else ' ' for c in a_str])).replace('\n', ' ').replace('\x0b', ' ')\
        .replace('\x0c', ' ').replace('\r', ' ').replace('\t', ' ').replace('!', ' ')

def read_header(data: bytes) -> Tuple[str, int]:
    filename = data[39:data.find(b'.xml')+4].decode('utf-8')
    filename_end = data.find(b'.xml')+4
    return filename, filename_end

def split_chunks(data: bytes, return_on_error: bool=False) -> Tuple[list, list]:
    chunks = [chunk.strip() for chunk in data.split(' ' * 18) if chunk.strip() != '']
    chunk_positions = []
    for chunk in chunks:
        found = data.find(chunk)
        if found == -1:
            print("Error: chunk not found during position check:", chunk)
            if return_on_error:
                return None, None
            continue
        chunk_positions.append((found-18, found + len(chunk)+6)) # start 18 bytes earlier to include extra data - not sure what it does, but if it works...
    return chunks, chunk_positions

def get_num_children(data: bytes) -> int:
    data = data.replace(b'\r', b'\x00')
    if not int(data[1]):
        return int(data[-1])
    return int(data[1]) # used to have more complex logic... could probably be merged with the main parsing function

# region parse
def parse_cx(data: bytes, debug: bool=False, die_on_error: bool=False, return_on_error: bool=False, export_chunks: bool=False):
    filename, filename_end = read_header(data)
    orig_data = data[filename_end:] # keep a copy for later
    data = remove_non_ascii(data[filename_end:].decode('utf-8', errors='replace'))
    if debug:
        print("filename:", filename)
    
    chunks, chunk_positions = split_chunks(data, return_on_error=return_on_error or die_on_error)
    if chunks is None and return_on_error:
        return None, None
    if chunks is None and die_on_error:
        exit(1)
    if debug:
        print("chunk positions:", chunk_positions)

    tokens = {}
    j = 0
    chunks_res = []
    for chunk in chunks:
        parts = chunk.split(' ' * 10, 1)
        orig_chunk = orig_data[chunk_positions[j][0]:chunk_positions[j][1]]
        tag = parts[0]
        token_index = int(orig_chunk[5])
        num_children = get_num_children(orig_chunk[-6:])
        tokens[tag] = {}
        tokens[tag]['_self_closing'] = orig_chunk[-6:].replace(b'\r', b'\x00') == b'\x00\x00\x00\x00\x00'
        tokens[tag]['_index'] = token_index
        tokens[tag]['_num_children'] = num_children
        chunks_res.append((chunk, orig_chunk, token_index, num_children))
        if debug:
            print("pos:", chunk_positions[j][0], chunk_positions[j][1])
            print("chunk:", chunk)
            print("bytes:", orig_chunk)
            print("token index:", token_index)
            print("num children:", num_children)
        if len(parts) > 1:
            attrs = parts[1].split(' ' * 6)
            i = 0
            if debug:
                print("attrs:", attrs)
            while i < len(attrs):
                key = attrs[i]
                try:
                    value = attrs[i+1]
                except IndexError:
                    print("Error: missing value for key:", key)
                    if return_on_error:
                        return None, None
                    if die_on_error:
                        exit(1)
                    break
                tokens[tag][key] = value
                i += 2
        j += 1
    if export_chunks:
        return chunks_res, filename
    root = list(tokens.keys())[0]
    tokens[root]['_num_children'] = -1
    return tokens, filename

# region transform
def transform(tokens: dict, debug: bool=False) -> dict:
    orig_tokens = tokens.copy()
    tokens = tokens.copy()
    root = list(tokens.keys())[0]
    del tokens[root]
    if debug:
        print("transform got", len(tokens), "tokens")
    transformed_tokens = {}
    index_to_key = {}
    for key, value in tokens.items():
        if not value["_self_closing"] and value["_num_children"] > 0:
            if debug:
                print("found tag with children:", key, value)
            value["_children"] = {}
    for key, value in tokens.items():
        if "_children" in value:
            for child_key, child_value in tokens.items():
                if child_value["_index"] > value["_index"] and child_value["_index"] <= value["_index"] + value["_num_children"]:
                    value["_children"][child_key] = child_value
                elif child_value["_index"] == value["_index"] and child_key != key:
                    if value["_index"] not in index_to_key:
                        index_to_key[value["_index"]] = key
                    else:
                        parent_key = index_to_key[value["_index"]]
                        tokens[parent_key]["_children"][child_key] = child_value
    for key, value in tokens.items():
        if "_index" in value and value["_index"] == 2:
            transformed_tokens[key] = value
            break
    if debug:
        print("restoring original top-level token:", root, orig_tokens[root])
    res = {root: orig_tokens[root]}
    res[root]["_children"] = transformed_tokens
    res[root]["_num_children"] = len(transformed_tokens)
    return res

# region to xml
def transformed_to_xml(tokens: dict, debug: bool=False, line_padding: str="") -> str:
    tokens_type = type(tokens)
    result = ""
    if tokens_type is list:
        for sub_elem in tokens:
            if debug:
                print("sub_elem:", sub_elem)
                print("line_padding:", line_padding)
            result += transformed_to_xml(sub_elem, debug=debug, line_padding=line_padding)
        return result
    if tokens_type is dict:
        xml = ""
        for tag_name in tokens:
            sub_obj = tokens[tag_name]
            attributes = ""
            for attr_name in sub_obj:
                if attr_name[0] != "_" and attr_name != "_children":
                    attributes += ' %s="%s"' % (attr_name, sub_obj[attr_name])
            xml += "%s<%s%s>" % (line_padding, tag_name, attributes)
            if "_children" in sub_obj:
                xml += "\n" + transformed_to_xml(sub_obj["_children"], debug=debug, line_padding="\t" + line_padding)
                xml += "%s</%s>\n" % (line_padding, tag_name)
            elif "_self_closing" in sub_obj and sub_obj["_self_closing"]:
                xml = xml[:-1] + "/>\n"
            else:
                xml += "\n"
                for attr_name in sub_obj:
                    if attr_name[0] != "_":
                        xml += '%s<%s>%s</%s>\n' % ("\t" + line_padding, attr_name, sub_obj[attr_name], attr_name)
                xml += "%s</%s>\n" % (line_padding, tag_name)
        return xml
    return "%s%s" % (line_padding, tokens)

def just_give_me_the_damn_xml(data: bytes):
    tokens, _ = parse_cx(data)
    return transformed_to_xml(transform(tokens))

# region main
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse, decode, and dump Tea for God .cx files')
    parser.add_argument('file', type=str, help='path to the .cx file')
    parser.add_argument('-o', '--output', type=str, help='path to the output file (default: original filename with .xml extension)')
    parser.add_argument('-j', '--json', action='store_true', help='output as JSON (closer to outputted tokens) instead of XML')
    parser.add_argument('-d', '--debug', action='store_true', help='print debug information')
    parser.add_argument('-D', '--dump', action='store_true', help='dump all file data without the header to a file (for debugging)')
    parser.add_argument('-c', '--chunks', action='store_true', help='output chunk data in a text file for comparison and research')
    parser.add_argument('-t', '--tokens', action='store_true', help='output untransformed tokens in JSON')
    parser.add_argument('-e', '--die-on-error', action='store_true', help='exit on any parsing error')
    args = parser.parse_args()

    if args.debug:
        print("args:", args)

    output = args.output
    if output is None and not args.dump:
        output = args.file[:args.file.find('.cx')] + ('.xml' if not args.json else '.json')
        if args.tokens:
            output = args.file[:args.file.find('.cx')] + '_tokens.json'
    elif args.dump:
        output = args.file[:args.file.find('.cx')] + '_dump.cx'

    if args.chunks:
        output = "./chunks.txt"

    with open(args.file, 'rb') as f:
        data = f.read()
        tokens, filename = parse_cx(data, debug=args.debug, die_on_error=args.die_on_error, export_chunks=args.chunks)
        if args.dump:
            with open(output, 'wb') as f:
                f.write(data[data.find(b'.xml')+4:])
        elif args.json:
            with open(output, 'w') as f:
                json.dump(transform(tokens, debug=args.debug), f, indent=4)
        elif args.tokens:
            with open(output, 'w') as f:
                json.dump(tokens, f, indent=4)
        elif args.chunks:
            with open(output, 'w') as f:
                for chunk in tokens:
                    f.write(str(chunk[2]) + " " + chunk[0] + '\n' + str(chunk[1]) + '\n\n')
        else:
            with open(output, 'w') as f:
                f.write(transformed_to_xml(transform(tokens, debug=args.debug), debug=args.debug))

    print(f'Output written to {output}')