# TeaRipper

Utilities for working with Tea for God assets, configuration files, and a modding framework

## Included Tools

- `teacx.py`: Utilities for working with `.cx` files, which are used to encode XML data for better load times
- `tearipper.py`: A multi-tool of sorts for extracting and modifying assets from Tea for God, as well as packaging and unpackaging mods

## Usage

See [docs/usage.md](docs/usage.md) for detailed usage instructions, and [docs/modding.md](docs/modding.md) for information on mods.

## Get Mods

Currently, there is no central repository for mods. However, you can find mods on the [Tea for God Discord](https://discord.gg/FFwyf4n).

## Installation

Prebuilt:

1. Download the latest release for your platform from the [releases page](https://github.com/N3rdL0rd/TeaRipper/releases)
2. Unzip the release to a directory of your choice
3. Add it to your PATH if you want to run the tools from anywhere, or leave them running from the directory
4. Run the tools as needed (`teacx`, `tearipper`)

All below options require Python 3.8 or higher to be installed.

From source:

1. Clone the repository
2. Run `pip install -r requirements.txt` to install the required dependencies
3. Run the tools as needed (`python teacx.py`, `python tearipper.py`)

Building executables:

1. Make sure you have `pyinstaller` installed (`pip install pyinstaller`)
2. Run `build.bat` to build the executables
3. The executables will be in the `dist` directory
4. Follow the prebuilt installation instructions from step 3

Packaging for release:

1. Make sure you have 7-Zip installed
2. Run `package.bat` to package the executables into a `.zip` file
3. The `.zip` file will be in the `dist` directory

## Roadmap

Short-term:

- [ ] Add support for install-time scripts in mods, and warn the user if they are present
- [ ] Create a GUI for the tools, possibly using [Dear PyGui](https://github.com/hoffstadt/DearPyGui)

Long-term:

- [ ] Add support for decoding other file formats, such as `.tex`
- [ ] Add mod dependency support
- [ ] Optimize mod size by using more complex binary diffing/patching algorithms

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgements

- [Tea for God](https://void-room.itch.io/tea-for-god) by [void room](https://void-room.itch.io/)
- [void room Discord](https://discord.gg/FFwyf4n) and void room himself for helping me understand the `.cx` format
- [ChatGPT](https://chatgpt.com/) for saving my ass on multiple occasions
