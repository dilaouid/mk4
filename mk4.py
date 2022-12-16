from pathlib import Path
import sys
import os
import subprocess
import configparser
import re

config = configparser.ConfigParser()
config.read('config.ini')

def documentation() -> None:
    print("documentation todo :) :) :) :) :) ;)")

def print_red(text: str) -> None:
    print(f"\033[31m{text}\033[0m")

# Get the file name without the extension
def get_file_name(filename: str) -> str:
    return os.path.splitext(filename)[0]

# generate a random name for the srt file
def get_subtitle_file() -> str:
    return "subtitle-" + str(os.urandom(6).hex()) + ".srt"

# Convert the mkv file to mp4 with the beautified srt file
def convert_file(filename: str, subtitles: str) -> None:
    print(f"    ⌛️ Converting file: \033[33m" + filename + "\033[0m to mp4 ...")
    output = Path(get_file_name(filename) + "-mk4.mp4")
    subprocess.run([
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-v", "error",
        "-stats",
        "-i", str(filename),
        "-vf", "subtitles=" + subtitles,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", config['FFMPEG']["CRF"],
        "-c:a", "aac",
        str(output)
    ])
    os.remove(subtitles)
    print(f"    ✅ File: \033[33m" + filename + "\033[0m has been converted")


# Check if the file has subtitles
def has_subtitles(filename: str) -> None:
    print(f"    ⌛️ Checking if file: \033[33m" + filename + "\033[0m has subtitles ...")
    result = subprocess.run(["ffmpeg", "-i", filename], capture_output=True, text=True)

    # Check if the file contains srts
    if "Subtitle:" in result.stderr or "subtitle:" in result.stdout:
        return True


# Extract the srt file from the mkv file
def extract_srt(filename: str, subtitle_file: str) -> None:
    print(f"    ⌛️ Extracting srt from \033[33m" + filename + "\033[0m ...")
    subprocess.run([
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-i", filename,
            "-c", "srt",
            "-map", "0:s:0",
            subtitle_file
    ])

# Beautify the srt file by adding font balises
def beautify_srt(filename: str) -> None:
    print(f"    ⌛️ Beautifying subtitles: \033[33m" + filename + "\033[0m ...")
    with open(filename, "r") as f:
        lines = f.readlines()
    formatted_lines = []
    line_num = 0

    # Add font balises to the srt file
    while line_num < len(lines):
        # Check if the line is a number (subtitle number)
        if lines[line_num].strip().isdigit():
            formatted_lines.append(lines[line_num])
            formatted_lines.append(lines[line_num + 1])
            line_num += 2
            dialog = ''
            # Add the dialog to the formatted line until we reach a new line
            while line_num < len(lines) and lines[line_num] != '\n':
                dialog += lines[line_num]
                line_num += 1
            # Add the font balises to the dialog and add it to the formatted lines list
            formatted_line = "<font size='{}' face='{}'>{}</font>".format(config['FONT']["Size"], config["FONT"]["Name"], dialog)
            formatted_lines.append(formatted_line)
            formatted_lines.append('\n\n')
        else:
            line_num += 1
    with open(filename, "w") as f:
        # Write the formatted lines to the srt file
        for line in formatted_lines:
            f.write(line)

    print(f"    ✅ \033[33m" + filename + "\033[0m has been beautified")

# Remove font balises from the srt file
def remove_font_balise(subtitle_file: str) -> None:
    print(f"    ⌛️ Removing font balises from file: \033[33m" + subtitle_file + "\033[0m ...")
    with open(subtitle_file, "r") as f:
        lines = f.read()

    # Remove font balises from the srt file (if any) to avoid double font balises in the final file
    pattern = r"<font.*?>|</font>"
    lines = re.sub(pattern, "", lines)

    with open(subtitle_file, "w") as f:
        f.write(lines)
    print(f"    ✅ Font balises has been removed from file: \033[33m" + subtitle_file+"\033[0m")

# process to the conversion from mkv to mp4
def process(filename: str) -> None:
    subtitle_file = get_subtitle_file()

    if not has_subtitles(filename):
        print(f"    ❌ \033[33m" + filename + "\033[0m has no subtitles")
    else:
        print(f"    ✅ \033[33m" + filename + "\033[0m has subtitles")
        extract_srt(filename, subtitle_file)
        remove_font_balise(subtitle_file)
        beautify_srt(subtitle_file)
        convert_file(filename, subtitle_file)

def main() -> int:
    # check if the user has passed a file
    if (len(sys.argv) < 2):
        sys.exit(print_red("❌ Usage: mk4.py <file> [<file> ...] or mk4.py --help"))

    # check if the user has passed the --help flag
    if (sys.argv[1] == "--help"):
        sys.exit(documentation())

    # check if all the files are valid mkv files
    for i in range(1, len(sys.argv)):
        
        # if the argument is a directory, recursively check all the mkv files in the directory
        if (os.path.isdir(sys.argv[i])):
            for root, dirs, files in os.walk(sys.argv[i]):
                for file in files:
                    if (file.endswith(".mkv") or file.endswith(".MKV")):
                        print("Checking file: " + file + " ...")
                        process(os.path.join(root, file))
        # otherwise, the argument is a file, so check if it is a valid mkv file and process it
        else:
            filename = str(Path(sys.argv[i]))
            print("Checking file: " + filename + " ...")

            # check if the file exists
            if (not os.path.exists(filename) or not os.path.isfile(filename) or not os.access(filename, os.R_OK)):
                sys.exit(print_red("❌ {filename} does not exist"))

            # check if the file is a mkv file
            if (not filename.endswith(".mkv") and not filename.endswith(".MKV")):
                sys.exit(print_red("❌ {filename} is not a mkv file"))

            process(filename)

    return 0

if __name__ == '__main__':
    sys.exit(main())