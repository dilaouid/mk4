#!/usr/bin/env python3
"""
mk4 - MKV to MP4 converter with subtitle burning

This script converts MKV files to MP4 format, burning subtitles into the video.
You can choose the font and the size of the subtitles in the config file.
And you can also select the correct subtitles and/or audio streams from the mkv file.
"""
import sys
import os
from pathlib import Path

from lib.utils import logger, is_ffmpeg_installed, validate_mkv_file, find_mkv_files
from lib.conversion import process_file

def show_documentation():
    """Display documentation and usage instructions"""
    logger.info("""
mk4 - I want it to be mp4

USAGE:
  mk4.py <file.mkv | directory> [<file.mkv | directory> ...]
  mk4.py --help

OPTIONS:
  -r    : Delete the original mkv after conversion
  --gui : Launch the graphical user interface

This script converts MKV files to MP4 format, burning subtitles into the video.
You can choose the font and the size of the subtitles in the config.ini file.

EXAMPLES:
  # Convert a single file
  mk4.py movie.mkv
  
  # Convert a single file and delete the original
  mk4.py movie.mkv -r
  
  # Convert all MKV files in a directory
  mk4.py /path/to/videos/
  
  # Convert multiple files and directories
  mk4.py movie1.mkv movie2.mkv /path/to/more/videos/
    """)
    sys.exit(0)

def main():
    """Main entry point for mk4 CLI"""
    # Check if ffmpeg is installed
    if not is_ffmpeg_installed():
        logger.error("❌ Ffmpeg is not installed, please install it before using mk4.py")
        sys.exit(1)

    # Check arguments
    if len(sys.argv) < 2:
        logger.error("❌ Usage: mk4.py <file> [<file> ...] or mk4.py --help")
        sys.exit(1)

    # Check for help flag
    if sys.argv[1] == "--help":
        show_documentation()
    
    # Check for GUI flag
    if sys.argv[1] == "--gui":
        try:
            from lib.gui.app import run_gui
            run_gui()
            return 0
        except ImportError:
            logger.error("❌ GUI mode requires PyQt5. Please install it with: pip install PyQt5")
            sys.exit(1)

    # Process arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "-r":
            i += 1
            continue

        # Delete file after conversion if -r flag is present
        delete_after = (i + 1 < len(args) and args[i + 1] == "-r")

        if os.path.isdir(arg):
            # Process directory
            mkv_files = find_mkv_files(arg)
            if not mkv_files:
                logger.warning(f"⚠️ No MKV files found in directory: {arg}")
            
            for file_path in mkv_files:
                logger.info(f"Checking file: {file_path}")
                process_file(file_path, delete_after)
        else:
            # Process single file
            file_path = str(Path(arg))
            logger.info(f"Checking file: {file_path}")
            
            if not validate_mkv_file(file_path):
                logger.error(f"❌ {file_path} does not exist, is not accessible, or is not an MKV file")
                sys.exit(1)
            
            process_file(file_path, delete_after)
        
        i += 1

    return 0

if __name__ == '__main__':
    sys.exit(main())