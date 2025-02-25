from pathlib import Path
import shutil
import sys
import os

from lib.utils import print_red, print_error
from lib.conversion import process_file

from rich.console import Console

console = Console()

def documentation() -> None:
    console.print("Documentation: \n"
                  "  Usage: mk4.py <file> [<file> ...] or mk4.py --help\n"
                  "  Options:\n"
                  "    -r    : Delete the original mkv after conversion\n"
                  "  Ce script convertit un fichier mkv en mp4 en extrayant et en embellissant les sous-titres.")
    sys.exit(0)

def main() -> int:
    # check if ffmpeg is installed
    if not shutil.which("ffmpeg"):
        sys.exit(print_error("❌ Ffmpeg is not installed, please install it before using mk4.py"))

    # check arguments
    if len(sys.argv) < 2:
        sys.exit(print_error("❌ Usage: mk4.py <file> [<file> ...] or mk4.py --help"))

    if sys.argv[1] == "--help":
        documentation()

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "-r":
            i += 1
            continue

        # delete file after conversion if -r flag is present
        delete_after = (i + 1 < len(args) and args[i + 1] == "-r")

        if os.path.isdir(arg):
            for root, dirs, files in os.walk(arg):
                for file in files:
                    if file.lower().endswith(".mkv"):
                        file_path = os.path.join(root, file)
                        console.print(f"Checking file: [yellow]{file}[/yellow] ...")
                        process_file(file_path, delete_after)
        else:
            file_path = str(Path(arg))
            console.print(f"Checking file: [yellow]{file_path}[/yellow] ...")
            if not (os.path.exists(file_path) and os.path.isfile(file_path) and os.access(file_path, os.R_OK)):
                sys.exit(print_error(f"❌ {file_path} does not exist or is not accessible"))
            if not file_path.lower().endswith(".mkv"):
                sys.exit(print_error(f"❌ {file_path} is not a mkv file"))
            process_file(file_path, delete_after)
        i += 1

    return 0

if __name__ == '__main__':
    sys.exit(main())