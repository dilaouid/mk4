# Convert the mkv file to mp4 with the beautified srt file and select the audio track
import sys
import os
from pathlib import Path
import subprocess
from lib.subtitles import beautify_srt, extract_srt, has_subtitles, remove_font_balise
from lib.utils import delete_mkv, get_file_name, get_subtitle_file, print_error
from lib.config import config
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TimeRemainingColumn, TextColumn

console = Console()

def get_video_duration(filename: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", filename
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    try:
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def time_str_to_seconds(time_str: str) -> float:

    try:
        parts = time_str.split(':')
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    except Exception:
        return 0.0

def convert_file(filename: str, subtitles: str) -> None:
    # get the duration of the video for the progress bar
    duration = get_video_duration(filename)
    if duration == 0:
        console.print("[red]Impossible de déterminer la durée de la vidéo. La barre de progression pourrait être incorrecte.[/red]")
        duration = 1  # Pour éviter la division par zéro

    console.print(f"    ⌛️ Converting file: [yellow]{filename}[/yellow] to mp4 ...")

    # audio track selection
    result = subprocess.run(["ffmpeg", "-i", filename],
                            capture_output=True, text=True)
    audio_tracks = [line for line in result.stderr.splitlines()
                    if "Audio:" in line or "audio:" in line]
    if len(audio_tracks) > 1:
        console.print(f"    ⌛️ [yellow]{filename}[/yellow] has multiple audio tracks, please select one:")
        for i, line in enumerate(audio_tracks):
            console.print(f"            [yellow]{i}[/yellow]: {line}")
        while True:
            try:
                selected_audio = int(console.input("    Please select the audio track you want to use: "))
                if selected_audio < 0 or selected_audio >= len(audio_tracks):
                    print_error("    ❌ Please select a valid audio track")
                else:
                    break
            except ValueError:
                print_error("    ❌ Please select a valid audio track")
        audio_track = f"0:a:{selected_audio}"
    else:
        audio_track = "0:a:0"

    output = Path(get_file_name(filename) + "-mk4.mp4")
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-i", str(filename),
        "-vf", "subtitles=" + subtitles,
        "-c:v", config['FFMPEG']["ENCODER"],
        "-pix_fmt", "yuv420p",
        "-crf", config['FFMPEG']["CRF"],
        "-c:a", "aac",
        "-map", audio_track,
        "-map", "0:v:0",
        str(output),
        "-progress", "pipe:1"
    ]

    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True)

    # use a progress bar to show the conversion progress
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),  # show percentage
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Converting...", total=duration)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            if line.startswith("out_time="):
                time_str = line.strip().split("=")[1]
                current_time = time_str_to_seconds(time_str)
                progress.update(task, completed=current_time)
            elif line.startswith("progress=end"):
                progress.update(task, completed=duration)
                break


    process.wait()
    os.remove(subtitles)
    console.print(f"    ✅ File: [yellow]{filename}[/yellow] has been converted")


# process to the conversion from mkv to mp4
def process_file(filename: str, delete_after: bool) -> None:
    subtitle_file = get_subtitle_file()

    if not has_subtitles(filename):
        console.print(f"    ❌ [yellow]{filename}[/yellow] has no subtitles")
    else:
        try:
            console.print(f"    ✅ [yellow]{filename}[/yellow] has subtitles")
            extract_srt(filename, subtitle_file)
            remove_font_balise(subtitle_file)
            beautify_srt(subtitle_file)
            convert_file(filename, subtitle_file)
            if delete_after:
                delete_mkv(filename)
        except KeyboardInterrupt:
            print_error("    ❌ Conversion cancelled")
            mk4_filename = Path(get_file_name(filename) + "-mk4.mp4")
            if os.path.exists(subtitle_file):
                os.remove(subtitle_file)
            if os.path.exists(mk4_filename):
                os.remove(mk4_filename)
            sys.exit(1)
        except Exception as e:
            print_error(f"    ❌ Failed to process file: {filename}")
            print_error(f"    ❌ Error: {str(e)}")
            sys.exit(1)
