# Florensia PAK Editor
Tool that allows viewing and editing the files inside a .pak file for the game Florensia.

## Features
- Can be set as the default application for .pak files (will only work for .pak files for Florensia, no other games)
- Export all (or a subset) of files inside a .pak file
- Delete files from the .pak archive
- Add files to the .pak archive
- Preview for text (`.txt`, `.xml`) as well as images (`.jpeg`, `.jpg`, `.png`, `.tga`, `.dds`, `.bmp`)
- Preview and export functions for `.bin` and `.dat` files

## Requirements
- Python `^3.12`
- Poetry `^1.8.3`

## Build an executable
Using PyInstaller, an executable can be created using the command `pyinstaller "Florensia PAK Editor.spec"`. The executable can then be found inside the `/dist` folder.
