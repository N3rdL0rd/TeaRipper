# TeaRipper

Utilities to dump and extract assets from Tea for God

## Included Tools

- `teacx.py`: Utilities for working with `.cx` files, which are used to encode XML data for better load times

## Usage

### `teacx.py`

```plaintext
usage: teacx.py [-h] [-o OUTPUT] [-j] [-d] [-D] [-c] [-t] [-e] file

Parse, decode, and dump Tea for God .cx files

positional arguments:
  file                  path to the .cx file

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        path to the output file (default: original filename with .xml extension)
  -j, --json            output as JSON (closer to outputted tokens) instead of XML
  -d, --debug           print debug information
  -D, --dump            dump all file data without the header to a file (for debugging)
  -c, --chunks          output chunk data in a text file for comparison and research
  -t, --tokens          output untransformed tokens in JSON
  -e, --die-on-error    exit on any parsing error
```

## Installation

So far, this project has no dependencies outside of the Python standard library. To install, simply clone the repository and run the script you need.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgements

- [Tea for God](https://void-room.itch.io/tea-for-god) by [void room](https://void-room.itch.io/)
- [void room Discord](https://discord.gg/FFwyf4n) and void room himself for helping me understand the `.cx` format
- [ChatGPT](https://chatgpt.com/) for saving my ass on multiple occasions
