import sys
import re
import subprocess
from lib.utils import print_error
from lib.config import config
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Check if the file has subtitles
def has_subtitles(filename: str) -> None:
    console.print(f"    ⌛️ Checking if file: [yellow]{filename}[/yellow] has subtitles ...")
    result = subprocess.run(["ffmpeg", "-i", filename],
                            capture_output=True, text=True)
    return "Subtitle:" in result.stderr or "subtitle:" in result.stdout

# Extract the srt file from the mkv file
def extract_srt(filename: str, subtitle_file: str) -> None:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Extracting srt...", total=None)
        result = subprocess.run(["ffmpeg", "-i", filename],
                                capture_output=True, text=True)
        # get "Subtitle:" starting lines
        subtitles = [line for line in result.stderr.splitlines()
                     if "Subtitle:" in line or "subtitle:" in line]
        progress.update(task, completed=100)

    # if multiple subtitles, ask the user to select one
    if len(subtitles) > 1:
        console.print(f"    ⌛️ [yellow]{filename}[/yellow] has multiple subtitles, please select one:")
        for i, line in enumerate(subtitles):
            parts = line.split(':')
            language = parts[1].strip() if len(parts) > 1 else ""
            languages = language.split('(')
            code = languages[1][:-1].upper() if len(languages) > 1 and len(languages[1]) > 1 else "UNK"
            stream = f"({code}): {parts[2]}: {parts[3]}" if len(parts) >= 4 else line
            console.print(f"            [yellow]{i}[/yellow]: {stream}")
        while True:
            try:
                selected_subtitle = int(console.input("    Please select the subtitle you want to use: "))
                if selected_subtitle < 0 or selected_subtitle >= len(subtitles):
                    print_error("    ❌ Please select a valid subtitle")
                else:
                    break
            except ValueError:
                print_error("    ❌ Please select a valid subtitle")
    else:
        selected_subtitle = 0

    # extract the selected subtitle
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", filename,
        "-c", "srt",
        "-map", f"0:s:{selected_subtitle}",
        subtitle_file
    ])



# Beautify the srt file by adding font balises
def beautify_srt(subtitle_file: str) -> None:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Beautifying subtitles...", total=None)
        try:
            with open(subtitle_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            formatted_lines = []
            line_num = 0
            while line_num < len(lines):
                if lines[line_num].strip().isdigit():
                    # number of the subtitle
                    formatted_lines.append(lines[line_num])
                    if line_num + 1 < len(lines):
                        formatted_lines.append(lines[line_num + 1])
                    line_num += 2
                    dialog = ''
                    # group all dialog lines
                    while line_num < len(lines) and lines[line_num].strip() != "":
                        dialog += lines[line_num]
                        line_num += 1
                    # format dialog with font balises
                    formatted_line = (
                        f"<font size=\"{config['FONT']['Size']}\" face=\"{config['FONT']['Name']}\">"
                        f"{dialog}</font>\n\n"
                    )
                    formatted_lines.append(formatted_line)
                else:
                    line_num += 1
            with open(subtitle_file, "w", encoding="utf-8") as f:
                f.writelines(formatted_lines)
            progress.update(task, completed=100)
        except Exception as e:
            print_error(f"    ❌ Failed to beautify the subtitles: {subtitle_file}")
            print_error(f"    ❌ Error: {str(e)}")
            sys.exit(1)

# Remove font balises from the srt file
def remove_font_balise(subtitle_file: str) -> None:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Removing font balises...", total=None)
        try:
            with open(subtitle_file, "r", encoding="utf-8") as f:
                content = f.read()
            pattern = r"<font.*?>|</font>"
            content = re.sub(pattern, "", content)
            with open(subtitle_file, "w", encoding="utf-8") as f:
                f.write(content)
            progress.update(task, completed=100)
        except Exception as e:
            print_error(f"    ❌ Failed to remove font balises from subtitles: {subtitle_file}")
            print_error(f"    ❌ Error: {str(e)}")
            sys.exit(1)