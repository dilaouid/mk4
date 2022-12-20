from pathlib import Path
import shutil
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

# manage the -r flag
def delete_mkv(filename: str) -> None:
    print(f"    ⌛️ Deleting: \033[33m" + filename + "\033[0m ...")
    try:
        # delete the file if it's a valid mkv file
        if os.path.isfile(filename) and (filename.endswith(".mkv") or filename.endswith(".MKV")):
            os.remove(filename)
            print(f"    🗑️ \033[33m" + filename + "\033[0m has been deleted!")
    except Exception as e:
        print_red("❌ Failed to delete file: " + filename)
        print_red("❌ Error: " + str(e))
        exit(1)

# Get the file name without the extension
def get_file_name(filename: str) -> str:
    return os.path.splitext(filename)[0]

# generate a random name for the srt file
def get_subtitle_file() -> str:
    return "subtitle-" + str(os.urandom(6).hex()) + ".srt"

# Convert the mkv file to mp4 with the beautified srt file and select the audio track
def convert_file(filename: str, subtitles: str) -> None:
    try:
        print(f"    ⌛️ Converting file: \033[33m" + filename + "\033[0m to mp4 ...")

        # check if the mkv file have multiple audio tracks and ask the user which one to use
        result = subprocess.run(["ffmpeg", "-i", filename], capture_output=True, text=True)
        audio_tracks = [line for line in result.stderr.splitlines() if "Audio:" in line or "audio:" in line]
        if len(audio_tracks) > 1:
            print(f"    ⌛️ \033[33m" + filename + "\033[0m has multiple audio tracks, please select the one you want to use: ")
            for i, line in enumerate(audio_tracks):
                print(f"            \033[33m{i}\033[0m: {line}")
            while True:
                try:
                    selected_audio_track = int(input("    Please select the audio track you want to use: "))
                    if selected_audio_track < 0 or selected_audio_track >= len(audio_tracks):
                        print_red("    ❌ Please select a valid audio track")
                    else:
                        break
                except ValueError:
                    print_red("    ❌ Please select a valid audio track")
            audio_track = "0:a:" + str(selected_audio_track)
        else:
            audio_track = "0:a:0"
        
        output = Path(get_file_name(filename) + "-mk4.mp4")
        
        subprocess.run([
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-v", "error",
            "-stats",
            "-i", str(filename),
            "-vf", "subtitles=" + subtitles,
            "-c:v", config['FFMPEG']["ENCODER"],
            "-pix_fmt", "yuv420p",
            "-crf", config['FFMPEG']["CRF"],
            "-c:a", "aac",
            "-map", audio_track,
            "-map", "0:v:0",

            # keeping the below lines only for dev mode. please keep them commented
            # "-ss", "00:00:00",
            # "-to", "00:00:20",
            str(output)
        ])
        os.remove(subtitles)
        print(f"    ✅ File: \033[33m" + filename + "\033[0m has been converted")
    except Exception as e:
        print_red("    ❌ Failed to convert file: " + filename)
        print_red("    ❌ Error: " + str(e))
        exit(1)

# Check if the file has subtitles
def has_subtitles(filename: str) -> None:
    print(f"    ⌛️ Checking if file: \033[33m" + filename + "\033[0m has subtitles ...")
    result = subprocess.run(["ffmpeg", "-i", filename], capture_output=True, text=True)

    # Check if the file contains srts
    return "Subtitle:" in result.stderr or "subtitle:" in result.stdout


# Extract the srt file from the mkv file
def extract_srt(filename: str, subtitle_file: str) -> None:
    try:
        print(f"    ⌛️ Extracting srt from \033[33m" + filename + "\033[0m ...")

        # check all the subtitles in the mkv file
        result = subprocess.run(["ffmpeg", "-i", filename], capture_output=True, text=True)
        subtitles = [line for line in result.stderr.splitlines() if "Subtitle:" in line or "subtitle:" in line]

        # if there is more than one subtitle, ask the user which one to use for the mp4 video
        if len(subtitles) > 1:
            print(f"    ⌛️ \033[33m" + filename + "\033[0m has multiple subtitles, please select the one you want to use:")
            # get the subtitles list
            subtitles = [line for line in result.stderr.splitlines() if "Subtitle:" in line or "subtitle:" in line]

            # print the subtitles list
            for i, line in enumerate(subtitles):
                print(f"            \033[33m{i}\033[0m: {line}")

            # ask the user to select the subtitle
            while True:
                try:
                    selected_subtitle = int(input("    Please select the subtitle you want to use: "))
                    if selected_subtitle < 0 or selected_subtitle >= len(subtitles):
                        print_red("    ❌ Please select a valid subtitle")
                    else:
                        break
                except ValueError:
                    print_red("    ❌ Please select a valid subtitle")

            # extract the selected subtitle
            subprocess.run([
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel", "error",
                "-i", filename,
                "-c", "srt",
                "-map", "0:s:" + str(selected_subtitle),
                subtitle_file
            ])
        else:
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
    except Exception as e:
        print_red("    ❌ Failed to extract srt from: " + filename)
        print_red("    ❌ Error: " + str(e))
        exit(1)

# Beautify the srt file by adding font balises
def beautify_srt(filename: str) -> None:
    try:
        print(f"    ⌛️ Beautifying subtitles: \033[33m" + filename + "\033[0m ...")
        with open(filename, "r", encoding="utf-8") as f:
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
                formatted_line = "<font size=\"{}\" face=\"{}\">{}</font>".format(config['FONT']["Size"], config["FONT"]["Name"], dialog)
                formatted_lines.append(formatted_line)
                formatted_lines.append('\n\n')
            else:
                line_num += 1
        with open(filename, "w", encoding="utf-8") as f:
            # Write the formatted lines to the srt file
            for line in formatted_lines:
                f.write(line)

        print(f"    ✅ \033[33m" + filename + "\033[0m has been beautified")
    except Exception as e:
        print_red("    ❌ Failed to beautify the subtitles: " + filename)
        print_red("    ❌ Error: " + str(e))
        exit(1)

# Remove font balises from the srt file
def remove_font_balise(subtitle_file: str) -> None:
    try:
        print(f"    ⌛️ Removing font balises from file: \033[33m" + subtitle_file + "\033[0m ...")
        with open(subtitle_file, "r", encoding="utf-8") as f:
            lines = f.read()

        # Remove font balises from the srt file (if any) to avoid double font balises in the final file
        pattern = r"<font.*?>|</font>"
        lines = re.sub(pattern, "", lines)

        with open(subtitle_file, "w", encoding="utf-8") as f:
            f.write(lines)
        print(f"    ✅ Font balises has been removed from file: \033[33m" + subtitle_file+"\033[0m")
    except Exception as e:
        print_red("    ❌ Failed to remove font balises from subtitles: " + subtitle_file)
        print_red("    ❌ Error: " + str(e))
        exit(1)

# process to the conversion from mkv to mp4
def process(filename: str, delete: bool) -> None:
    subtitle_file = get_subtitle_file()

    if not has_subtitles(filename):
        print(f"    ❌ \033[33m" + filename + "\033[0m has no subtitles")
    else:
        try:
            print(f"    ✅ \033[33m" + filename + "\033[0m has subtitles")
            extract_srt(filename, subtitle_file)
            remove_font_balise(subtitle_file)
            beautify_srt(subtitle_file)
            convert_file(filename, subtitle_file)
            if delete:
                delete_mkv(filename)
        except KeyboardInterrupt:
            print_red("    ❌ Conversion cancelled")
            mk4_filename = Path(get_file_name(filename) + "-mk4.mp4")
            if os.path.exists(subtitle_file):
                os.remove(subtitle_file)
            if os.path.exists(mk4_filename):
                os.remove(mk4_filename)
            exit(1)
        except Exception as e:
            print_red("    ❌ Failed to process file: " + filename)
            print_red("    ❌ Error: " + str(e))
            exit(1)

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