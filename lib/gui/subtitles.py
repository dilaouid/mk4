"""
GUI-specific functions for subtitle handling
"""
import os
import re
import subprocess
from typing import Optional, Callable, Dict
from lib.utils import logger
from lib.config import config, DEFAULT_CONFIG

def analyze_file_streams(filename: str) -> Dict:
    """
    Analyze file streams (video, audio, subtitle) for debugging
    
    Args:
        filename: Path to the file
    
    Returns:
        Dict with information about streams
    """
    try:
        # Run ffprobe to get detailed stream information in JSON format
        result = subprocess.run([
            "ffprobe", 
            "-v", "quiet", 
            "-print_format", "json", 
            "-show_format", 
            "-show_streams", 
            filename
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to analyze file: {result.stderr}")
            return {"error": result.stderr}
        
        # Try to parse the JSON output
        import json
        try:
            info = json.loads(result.stdout)
            
            # Log stream types
            if "streams" in info:
                stream_types = {}
                for i, stream in enumerate(info["streams"]):
                    codec_type = stream.get("codec_type", "unknown")
                    if codec_type not in stream_types:
                        stream_types[codec_type] = []
                    stream_types[codec_type].append(i)
                
                logger.info(f"File streams: {stream_types}")
            
            return info
        except json.JSONDecodeError:
            logger.error("Failed to parse ffprobe JSON output")
            return {"error": "JSON parse error", "raw": result.stdout}
    
    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e)}

def has_subtitles_gui(filename: str) -> bool:
    """Check if the file has subtitles - GUI version"""
    logger.info(f"Checking if file has subtitles: {filename}")
    try:
        result = subprocess.run(["ffmpeg", "-i", filename],
                             capture_output=True, text=True)
        
        # Check if subtitles are mentioned in ffmpeg output
        has_subs = "Subtitle:" in result.stderr or "subtitle:" in result.stderr
        
        if has_subs:
            logger.info(f"Found subtitles in file: {filename}")
        else:
            logger.warning(f"No subtitles found in file: {filename}")
        
        # Additional checks using ffprobe
        file_info = analyze_file_streams(filename)
        if "streams" in file_info:
            subtitle_streams = [
                s for s in file_info["streams"] 
                if s.get("codec_type") == "subtitle"
            ]
            
            if subtitle_streams:
                logger.info(f"Found {len(subtitle_streams)} subtitle streams using ffprobe")
                # Log subtitle codec details
                for i, sub in enumerate(subtitle_streams):
                    logger.info(f"Subtitle {i}: codec={sub.get('codec_name', 'unknown')}, "
                               f"language={sub.get('tags', {}).get('language', 'unknown')}")
                return True
        
        return has_subs
    except Exception as e:
        logger.error(f"Error checking for subtitles: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def extract_srt_gui(filename: str, subtitle_file: str, subtitle_index: int, 
                progress_callback: Optional[Callable[[float], None]] = None) -> bool:
    """
    Extract the srt file from the mkv file - GUI version
    
    Args:
        filename: Path to the MKV file
        subtitle_file: Path to write the SRT file
        subtitle_index: Index of the subtitle track to extract
        progress_callback: Optional callback for progress updates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if progress_callback:
            progress_callback(0.1)
        
        logger.info(f"Extracting subtitle track {subtitle_index} from {filename}")
        
        # Check for PGS subtitle format which can't be converted to SRT
        file_info = analyze_file_streams(filename)
        if "streams" in file_info:
            subtitle_streams = [
                s for s in file_info["streams"] 
                if s.get("codec_type") == "subtitle"
            ]
            
            if len(subtitle_streams) > subtitle_index:
                codec = subtitle_streams[subtitle_index].get("codec_name", "")
                logger.info(f"Selected subtitle codec: {codec}")
                
                # Skip bitmap-based subtitles when SRT is expected
                if codec in ["hdmv_pgs_subtitle", "dvd_subtitle", "dvdsub"]:
                    logger.warning(f"Bitmap-based subtitle format detected: {codec}")
                    logger.warning("Cannot convert bitmap subtitles to SRT format")
                    logger.warning("Try using a text-based subtitle track")
                    return False
        
        # Try three different subtitle extraction methods
        
        # Method 1: Standard ffmpeg extraction
        process = subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", filename,
            "-c", "srt",
            "-map", f"0:s:{subtitle_index}",
            subtitle_file
        ], capture_output=True, text=True)
        
        if process.returncode == 0 and os.path.exists(subtitle_file) and os.path.getsize(subtitle_file) > 0:
            logger.info(f"Successfully extracted subtitles to: {subtitle_file}")
            if progress_callback:
                progress_callback(1.0)
            return True

        logger.error(f"Failed to extract subtitles: {process.stderr}")

        # Method 2: Direct extraction (no format conversion)
        logger.info("Trying direct subtitle extraction...")
        alt_process = subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", filename,
            "-map", f"0:s:{subtitle_index}",
            subtitle_file
        ], capture_output=True, text=True)

        if alt_process.returncode == 0 and os.path.exists(subtitle_file) and os.path.getsize(subtitle_file) > 0:
            logger.info("Direct extraction worked")
            if progress_callback:
                progress_callback(1.0)
            return True

        logger.error(f"Alternative extraction also failed: {alt_process.stderr}")
        logger.error("Cannot extract subtitles from this file/track")
        return False

    except Exception as e:
        logger.error(f"Exception in extract_srt: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def remove_font_balise_gui(subtitle_file: str, 
                       progress_callback: Optional[Callable[[float], None]] = None) -> bool:
    """
    Remove font balises from the srt file - GUI version
    
    Args:
        subtitle_file: Path to the SRT file
        progress_callback: Optional callback for progress updates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if progress_callback:
            progress_callback(0.1)
        
        with open(subtitle_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        pattern = r"<font.*?>|</font>"
        content = re.sub(pattern, "", content)
        
        if progress_callback:
            progress_callback(0.5)
        
        with open(subtitle_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        if progress_callback:
            progress_callback(1.0)
        
        return True
    except Exception as e:
        logger.error(f"Failed to remove font balises from subtitles: {str(e)}")
        return False

def beautify_srt_gui(subtitle_file: str, 
                progress_callback: Optional[Callable[[float], None]] = None) -> bool:
    """
    Beautify the srt file by adding font balises - GUI version
    
    Args:
        subtitle_file: Path to the SRT file
        progress_callback: Optional callback for progress updates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if progress_callback:
            progress_callback(0.1)
        
        # Get font settings with defaults
        font_size = "24"
        font_name = "Arial"
        
        try:
            if 'FONT' in config:
                if 'Size' in config['FONT']:
                    font_size = config['FONT']['Size']
                elif 'size' in config['FONT']:
                    font_size = config['FONT']['size']
                    
                if 'Name' in config['FONT']:
                    font_name = config['FONT']['Name']
                elif 'name' in config['FONT']:
                    font_name = config['FONT']['name']
        except Exception:
            # Fall back to defaults if anything goes wrong
            font_size = DEFAULT_CONFIG['FONT']['Size']
            font_name = DEFAULT_CONFIG['FONT']['Name']
        
        logger.info(f"Using font: {font_name}, size: {font_size}")
        
        with open(subtitle_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        formatted_lines = []
        line_num = 0
        total_lines = len(lines)
        
        while line_num < total_lines:
            # Look for subtitle number lines (just a number)
            if lines[line_num].strip().isdigit():
                # Add the subtitle number
                formatted_lines.append(lines[line_num])
                
                # Add the timestamp line
                if line_num + 1 < total_lines:
                    formatted_lines.append(lines[line_num + 1])
                line_num += 2
                
                # Collect all dialog lines until empty line
                dialog = ''
                while line_num < total_lines and lines[line_num].strip() != "":
                    dialog += lines[line_num]
                    line_num += 1
                
                # Format dialog with font balises, preserving any existing tags
                formatted_line = (
                    f"<font size=\"{font_size}\" face=\"{font_name}\">"
                    f"{dialog}</font>\n\n"
                )
                formatted_lines.append(formatted_line)
            else:
                # If it doesn't match our expected format, add the line as is
                formatted_lines.append(lines[line_num])
                line_num += 1
            
            if progress_callback and total_lines > 0:
                progress_callback(min(0.9, line_num / total_lines * 0.9))
        
        with open(subtitle_file, "w", encoding="utf-8") as f:
            f.writelines(formatted_lines)
        
        if progress_callback:
            progress_callback(1.0)
        
        return True
    except Exception as e:
        logger.error(f"Failed to beautify the subtitles: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False