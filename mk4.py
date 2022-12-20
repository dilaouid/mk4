from pathlib import Path
import shutil
import sys
import os
from lib.utils import print_red
from lib.conversion import process

def documentation() -> None:
    print("documentation todo :) :) :) :) :) ;)")

def main() -> int:

    # check if ffmpeg is installed
    if not shutil.which("ffmpeg"):
        sys.exit(print_red("❌ Ffmpeg is not installed, please install it before using mk4.py"))

    # check if the user has passed a file
    if len(sys.argv) < 2:
        sys.exit(print_red("❌ Usage: mk4.py <file> [<file> ...] or mk4.py --help"))

    # check if the user has passed the --help flag
    if sys.argv[1] == "--help":
        sys.exit(documentation())

    for i in range(1, len(sys.argv)):

        # if the argument is a -r flag, ignore it
        if sys.argv[i] == "-r":
            continue

        try:
            # check if the next argument is a -r
            delete = i + 1 < len(sys.argv) and sys.argv[i + 1] == "-r"
         
            # if the argument is a directory, recursively check all the mkv files in the directory
            if os.path.isdir(sys.argv[i]):
                for root, dirs, files in os.walk(sys.argv[i]):
                    for file in files:
                        if (file.endswith(".mkv") or file.endswith(".MKV")):
                            print("Checking file: " + file + " ...")
                            process(os.path.join(root, file), delete)
            # otherwise, the argument is a file, so check if it is a valid mkv file and process it
            else:
                filename = str(Path(sys.argv[i]))
                print("Checking file: " + filename + " ...")

                # check if the file exists
                if not os.path.exists(filename) or not os.path.isfile(filename) or not os.access(filename, os.R_OK):
                    sys.exit(print_red("❌ "+filename+" does not exist"))

                # check if the file is a mkv file
                if not filename.endswith(".mkv") and not filename.endswith(".MKV"):
                    sys.exit(print_red("❌ "+filename+" is not a mkv file"))

                process(filename, delete)
        except Exception as e:
            print_red("❌ Failed to process file: " + sys.argv[i])
            print_red("❌ Error: " + str(e))
            exit(1)
    return 0

if __name__ == '__main__':
    sys.exit(main())