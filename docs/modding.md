# Tea for God Modding: A Guide

This guide is a short tutorial for modding your copy of Tea for God. If you're looking to create a mod, continue reading. If you're looking to install a mod, skip to the [Using Mods](#using-mods) section.

## Disclaimer

This is not officially endorsed by void room. Modding is done at your own risk, and we are not responsible for any issues that may arise from modding.

This guide assumes you have already followed the installation instructions in the README.

## Creating a Mod

To create a mod, you first have to create a registry of your current game files so changes can be tracked. This action also decodes .cx files, which are encoded forms of XML, allowing you to edit them freely before repacking.

Open a command prompt in your game directory and run:

```plaintext
tearipper dump -m .
```

Note that the `-m` can be omitted if you don't plan to repack any game files. If you forget to pass `-m`, you can run `tearipper init` later to create the mod configuration file.

If everything works correctly, filenames from the game will scroll by, and you will be prompted to fill in some information about your mod. Do so until the text `Done!` is printed in blue. If you experience an error, please contact N3rdL0rd on Discord (you can find me in the void room server).

After the dump is complete, each cx file will have a corresponding decoded XML file. You can now edit these files to your heart's content. A dump.teareg file will also be created, which is a registry of all the files in the game, along with a mod configuration file, `<your mod id>.mod.json`.

Now that you've dumped your files, make any changes you want to the game files. Some file formats will have been automatically decoded, but note that the game will not load their unpacked versions directly - you must place them in the _source directory relative to their original locations if you want the game to correctly load them.

Once you've made your changes, you can package the modified game files by running:

```plaintext
tearipper package .
```

This will create a new teamod file for your mod, which you can then share with others.

## Using Mods

To use a mod, you must first have a teamod file. If you have a teamod file, you can install it by running:

```plaintext
tearipper unpackage <path to teamod file> <path to game files>
```

If you want to only temporarily use a mod, you can use the `play` subcommand:

```plaintext
tearipper play <path to game files> <path to folder containing teamod file(s)>
```

A graphical user interface for managing mods is planned, and is in the works.
