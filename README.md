# mk4

![preview](https://pbs.twimg.com/media/FkISQIGWYAYLWpC?format=jpg&name=large)

## _I want it to be mp4_

mk4 is a Python 3 tool to convert MKV videos into MP4, and burn subtitles into the MP4 output. You can choose the font and the size of the subtitles in the config file. And you can also select the correct subtitles and/or audio streams from the MKV file.

## Features

- Convert MKV videos to MP4 format
- Burn subtitles directly into the video
- Select specific subtitle and audio tracks
- Customize subtitle font and size
- Batch process multiple files
- Both command-line and graphical interfaces

## Screenshots

![GUI Screenshot](https://example.com/screenshot.png)

## Prerequisites

- Python 3.6+
- FFmpeg installed in your system PATH
- PyQt5 (for the GUI version): `pip install PyQt5`

## Installation

1. Clone the repository or download the source code
2. Install PyQt5 if you want to use the GUI: `pip install PyQt5`
3. Make sure FFmpeg is installed and available in your system PATH

## Usage

### Command-Line Interface

```bash
# Basic usage
python mk4.py <file.mkv | directory> [<file.mkv | directory> ...]

# Convert a single file
python mk4.py movie.mkv

# Convert a single file and delete the original
python mk4.py movie.mkv -r

# Convert all MKV files in a directory
python mk4.py /path/to/videos/

# Show help
python mk4.py --help
```

### Graphical User Interface

```bash
# Launch the GUI
python mk4_gui.py

# Or from the CLI script
python mk4.py --gui
```

## GUI Features

- Drag and drop MKV files for conversion
- Select output directory
- Choose subtitle and audio tracks
- Configure encoding settings
- Real-time conversion progress
- Light and dark themes

## Configuration

You can configure mk4 through the GUI Settings tab or by editing the `config.ini` file directly:

```ini
[FFMPEG]
encoder = libx264
crf = 23
ENCODER = libx264
CRF = 23

[FONT]
size = 24
name = Arial
SIZE = 24
NAME = Arial

[GUI]
theme = dark
language = en
autodeletemkv = False
THEME = dark
LANGUAGE = en
AUTODELETEMKV = False
```

### Configuration Options

- **ENCODER**: Video encoder to use (libx264, libx265, h264_nvenc, etc.)
- **CRF**: Constant Rate Factor (0-51, lower is better quality)
- **Size**: Font size for subtitles
- **Name**: Font name for subtitles
- **Theme**: GUI theme (light or dark)
- **AutoDeleteMKV**: Whether to automatically delete MKV files after conversion
