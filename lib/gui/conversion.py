"""
GUI-specific functions for video conversion
"""
import os
import re
import time
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Callable, Dict

from lib.gui.subtitles import (
    has_subtitles_gui, extract_srt_gui,
    remove_font_balise_gui, beautify_srt_gui
)
from lib.utils import (
    logger, get_file_name, get_subtitle_file, delete_mkv, get_output_path
)
from lib.config import config

class AudioTrack:
    """Class representing an audio track"""
    def __init__(self, index: int, language: str, description: str):
        self.index = index
        self.language = language
        self.description = description
    
    def __str__(self) -> str:
        return f"({self.language}): {self.description}"

def get_video_duration(filename: str) -> float:
    """
    Get the duration of a video file in seconds
    
    Args:
        filename: Path to the video file
        
    Returns:
        float: Duration in seconds, 0 if failed
    """
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
    """
    Convert a time string (HH:MM:SS.MS) to seconds
    
    Args:
        time_str: Time string in format HH:MM:SS.MS
        
    Returns:
        float: Time in seconds
    """
    try:
        parts = time_str.split(':')
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    except Exception:
        return 0.0

def get_audio_tracks(filename: str) -> List[AudioTrack]:
    """
    Get all audio tracks from a file
    
    Args:
        filename: Path to the video file
        
    Returns:
        List[AudioTrack]: List of audio tracks
    """
    result = subprocess.run(["ffmpeg", "-i", filename],
                          capture_output=True, text=True)
    audio_tracks = [line for line in result.stderr.splitlines()
                  if "Audio:" in line or "audio:" in line]
    
    tracks = []
    for i, line in enumerate(audio_tracks):
        parts = line.split(':')
        language = parts[1].strip() if len(parts) > 1 else ""
        languages = language.split('(')
        code = languages[1][:-1].upper() if len(languages) > 1 and len(languages[1]) > 1 else "UNK"
        description = f"{parts[2]}: {parts[3]}" if len(parts) >= 4 else line
        tracks.append(AudioTrack(i, code, description))
    
    return tracks

def convert_file_gui(
    filename: str, subtitles: str, 
    audio_index: int = 0,
    output_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float], None]] = None
) -> bool:
    """
    Convert MKV file to MP4 with subtitles - GUI version
    
    Args:
        filename: Path to the MKV file
        subtitles: Path to the SRT file
        audio_index: Index of the audio track to use
        output_path: Path to save the MP4 file (default: same directory as input)
        progress_callback: Optional callback for progress updates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Show initial progress
        if progress_callback:
            progress_callback(0.05)
        
        # Get the duration of the video
        duration = get_video_duration(filename)
        if duration == 0:
            logger.warning("Unable to determine video duration. Progress might be incorrect.")
            duration = 1  # To avoid division by zero
        
        logger.info(f"Converting file: {filename} to mp4...")
        
        # Determine output path
        if output_path:
            output = Path(output_path)
        else:
            # Create output in same directory as input
            output = Path(get_file_name(filename) + "-mk4.mp4")
        
        logger.info(f"Output will be saved to: {output}")
        
        # Check subtitle file
        if not os.path.exists(subtitles):
            logger.error(f"Subtitle file does not exist: {subtitles}")
            return False
        
        if os.path.getsize(subtitles) == 0:
            logger.error(f"Subtitle file is empty: {subtitles}")
            return False
        
        # Get encoder and CRF settings from config
        encoder = "libx264"  # Default
        crf = "23"  # Default
        
        try:
            if 'FFMPEG' in config:
                if 'ENCODER' in config['FFMPEG']:
                    encoder = config['FFMPEG']['ENCODER']
                elif 'encoder' in config['FFMPEG']:
                    encoder = config['FFMPEG']['encoder']
                
                if 'CRF' in config['FFMPEG']:
                    crf = config['FFMPEG']['CRF']
                elif 'crf' in config['FFMPEG']:
                    crf = config['FFMPEG']['crf']
        except Exception as e:
            logger.warning(f"Using default encoding settings: {str(e)}")
        
        logger.info(f"Using encoder: {encoder}")
        logger.info(f"Using CRF: {crf}")
        
        # Subtitles method 1: direct embedding with map
        logger.info("Using direct subtitle embedding method")
        
        # Ensure paths are properly formatted for ffmpeg
        safe_filename = str(Path(filename).resolve()).replace("\\", "/")
        safe_subtitles = str(Path(subtitles).resolve()).replace("\\", "/").replace(":", "\\:")
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-i", safe_filename,
            "-vf", f"subtitles='{safe_subtitles}'",
            "-pix_fmt", "yuv420p",
            "-map", "0:v:0",
            "-map", f"0:a:{audio_index}",
            "-c:v", encoder,
            "-crf", crf,
            "-c:a", "aac",
            str(output)
        ]

        logger.info(f"Running command: {' '.join(str(arg) for arg in ffmpeg_cmd)}")
        
        if progress_callback:
            progress_callback(0.1)
        
        # Start conversion process
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            text=True
        )
        
        # Need to update progress in real-time
        start_time = time.time()
        last_progress_time = start_time
        
        # For storing output
        stderr_output = ""
        
        # Monitor process and update progress
        while process.poll() is None:
            # Check stderr for "time=" updates which indicate progress
            if process.stderr:
                line = process.stderr.readline()
                if line:
                    stderr_output += line
                    # Look for time= which is how ffmpeg reports progress
                    if "time=" in line:
                        # Extract time
                        time_match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                        if time_match:
                            # Convert to seconds
                            current_time = time_str_to_seconds(time_match.group(1))
                            if duration > 0:
                                progress_value = min(0.95, current_time / duration)
                                if progress_callback:
                                    progress_callback(progress_value)
                                    last_progress_time = time.time()
            
            # If no progress for 2 seconds, update progress slightly to show activity
            current_time = time.time()
            if current_time - last_progress_time > 2.0 and progress_callback:
                last_progress_time = current_time
                # Calculate fake progress based on elapsed time (max 95%)
                elapsed = current_time - start_time
                fake_progress = min(0.95, elapsed / (duration * 2))  # Assume conversion takes twice video duration
                progress_callback(fake_progress)
            
            # Don't hog CPU
            time.sleep(0.1)
        
        # Process finished - get return code
        return_code = process.wait()
        
        # Make sure to read any remaining output
        if process.stderr:
            remaining = process.stderr.read()
            stderr_output += remaining
        
        # Set progress to 100%
        if progress_callback:
            progress_callback(1.0)
        
        # Check if successful
        if return_code != 0:
            logger.error(f"Conversion failed: {stderr_output}")
            
            # Try method 2: subtitle filter approach
            logger.info("Trying alternate subtitle method...")
            
            subtitle_filter_cmd = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-i", str(filename),
                "-vf", f"subtitles={subtitles}",
                "-c:v", encoder,
                "-pix_fmt", "yuv420p",
                "-crf", crf,
                "-c:a", "aac",
                "-map", f"0:a:{audio_index}",
                "-map", "0:v:0",
                str(output)
            ]
            
            logger.info(f"Running alternate command: {' '.join(str(arg) for arg in subtitle_filter_cmd)}")
            
            # Run alternate command in blocking mode (simpler)
            alt_process = subprocess.run(subtitle_filter_cmd, capture_output=True, text=True)
            
            if alt_process.returncode != 0:
                logger.error(f"Alternate conversion failed: {alt_process.stderr}")
                
                # Method 3: fallback to no subtitles
                logger.warning("Trying final method without subtitles...")
                
                no_subs_cmd = [
                    "ffmpeg",
                    "-y",
                    "-hide_banner",
                    "-i", str(filename),
                    "-c:v", encoder,
                    "-pix_fmt", "yuv420p",
                    "-crf", crf,
                    "-c:a", "aac",
                    "-map", f"0:a:{audio_index}",
                    "-map", "0:v:0",
                    str(output)
                ]
                
                logger.info(f"Running final command: {' '.join(str(arg) for arg in no_subs_cmd)}")
                
                # Run final command
                final_process = subprocess.run(no_subs_cmd, capture_output=True, text=True)
                
                if final_process.returncode != 0:
                    logger.error(f"Final conversion failed: {final_process.stderr}")
                    return False
                
                logger.warning("Converted without subtitles (fallback method)")
                
                # Clean up subtitle file
                if os.path.exists(subtitles):
                    os.remove(subtitles)
                
                return True
            
            logger.info("Alternate conversion succeeded")
            
            # Clean up subtitle file
            if os.path.exists(subtitles):
                os.remove(subtitles)
            
            return True
        
        # Clean up subtitle file
        if os.path.exists(subtitles):
            os.remove(subtitles)
        
        logger.info(f"Conversion completed successfully: {output}")
        return True
    
    except Exception as e:
        logger.error(f"Exception in convert_file_gui: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def process_file_gui(
    filename: str, 
    delete_after: bool = False,
    subtitle_index: Optional[int] = None,
    audio_index: Optional[int] = None,
    output_path: Optional[str] = None,
    progress_callback: Optional[Callable[[Dict[str, float]], None]] = None
) -> bool:
    """
    Process a single MKV file (extract subtitles, convert to MP4) - GUI version
    
    Args:
        filename: Path to the MKV file
        delete_after: Whether to delete the MKV file after conversion
        subtitle_index: Index of the subtitle track to use
        audio_index: Index of the audio track to use
        output_path: Path to save the MP4 file
        progress_callback: Optional callback for progress updates
        
    Returns:
        bool: True if successful, False otherwise
    """
    subtitle_file = get_subtitle_file()
    
    try:
        # Check if file has subtitles
        if not has_subtitles_gui(filename):
            logger.error(f"File has no subtitles: {filename}")
            return False
        
        logger.info(f"File has subtitles: {filename}")
        
        # Track progress for each step
        total_steps = 4  # extract, remove, beautify, convert
        current_step = 0
        
        def update_progress(step_name: str, progress: float) -> None:
            if progress_callback:
                nonlocal current_step
                # Calculate overall progress 
                overall = (current_step + progress) / total_steps
                progress_callback({
                    "step": step_name,
                    "step_progress": progress,
                    "overall_progress": overall
                })
        
        # Extract subtitles
        current_step = 0
        update_progress("Extracting subtitles", 0)
        logger.info(f"Extracting subtitles from: {filename}")
        
        if subtitle_index is None:
            subtitle_index = 0
        
        if not extract_srt_gui(
            filename, 
            subtitle_file, 
            subtitle_index,
            lambda p: update_progress("Extracting subtitles", p)
        ):
            logger.error(f"Failed to extract subtitles from: {filename}")
            return False
        
        # Remove font balises
        current_step = 1
        update_progress("Removing font balises", 0)
        logger.info(f"Removing font balises from subtitles")
        if not remove_font_balise_gui(
            subtitle_file,
            lambda p: update_progress("Removing font balises", p)
        ):
            logger.error("Failed to remove font balises")
            return False
        
        # Beautify subtitles
        current_step = 2
        update_progress("Beautifying subtitles", 0)
        logger.info(f"Beautifying subtitles")
        if not beautify_srt_gui(
            subtitle_file,
            lambda p: update_progress("Beautifying subtitles", p)
        ):
            logger.error("Failed to beautify subtitles")
            return False
        
        # Convert file
        current_step = 3
        update_progress("Converting file", 0)
        logger.info(f"Starting file conversion from {filename} to MP4")
        
        if audio_index is None:
            audio_index = 0
        
        if not convert_file_gui(
            filename, 
            subtitle_file, 
            audio_index,
            output_path,
            lambda p: update_progress("Converting file", p)
        ):
            logger.error("Failed in the convert_file step")
            return False
        
        # Delete original file if requested
        if delete_after:
            delete_mkv(filename)
        
        return True
    
    except KeyboardInterrupt:
        logger.error("Conversion cancelled")
        # Clean up temp files
        if os.path.exists(subtitle_file):
            os.remove(subtitle_file)
        output_file = Path(output_path) if output_path else Path(get_file_name(filename) + "-mk4.mp4")
        if os.path.exists(output_file):
            os.remove(output_file)
        return False
    
    except Exception as e:
        logger.error(f"Failed to process file: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Clean up temp files
        if os.path.exists(subtitle_file):
            os.remove(subtitle_file)
        return False