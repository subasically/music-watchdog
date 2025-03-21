import math
import os
import re
import shutil
import requests  # added import for downloading cover image
import subprocess
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from pydub import AudioSegment
import logger as logger

log = logger.logger  # shared logger


def try_int(s):
    try:
        return int(s)
    except:
        return s


def alphanum_key(s):
    return [try_int(c) for c in re.split("([0-9]+)", s)]


def update_mp3_metadata(file_path, track_data=None, title=None, artist=None, cover_path=None):
    # If track_data is provided, use its values as defaults
    if track_data:
        title = title or track_data.get("title")
        artist = artist or track_data.get("subtitle")
        cover_path = cover_path or track_data.get("images", {}).get("coverart")
    log.debug(f"Updating metadata for file: {file_path}")
    cover_data = None
    if cover_path:
        if cover_path.startswith("http"):
            log.debug(f"Downloading cover from {cover_path}")
            try:
                r = requests.get(cover_path, timeout=10)
                if r.status_code == 200:
                    cover_data = r.content
                else:
                    log.warning(
                        f"Failed to download cover from {cover_path}: {r.status_code}")
            except Exception as e:
                log.warning(
                    f"Exception downloading cover from {cover_path}: {e}")
        elif os.path.exists(cover_path):
            with open(cover_path, "rb") as img:
                log.debug(f"Reading cover from {cover_path}")
                cover_data = img.read()
            os.remove(cover_path)
    # Use ID3 if cover data is present; otherwise EasyID3.
    use_id3 = True if cover_data else False
    try:
        if use_id3:
            audio = ID3(file_path)
        else:
            audio = EasyID3(file_path)
    except Exception:
        log.debug("No existing tag found, creating new tag")
        audio = ID3(file_path)
        use_id3 = True
        log.debug(f"Adding title: {title}")
        audio.add(TIT2(encoding=3, text=title))
        log.debug(f"Adding artist: {artist}")
        audio.add(TPE1(encoding=3, text=artist))
        if cover_data:
            log.debug("Adding cover image")
            audio.add(APIC(encoding=3, mime="image/jpeg",
                      type=3, desc="Cover", data=cover_data))
        audio.save(v2_version=3)
        log.info(f"Metadata added for {file_path} (new tag)")
        return
    log.debug("Updating existing metadata")
    if use_id3:
        audio.delall("TIT2")
        log.debug(f"Setting title: {title}")
        audio.add(TIT2(encoding=3, text=title))
        audio.delall("TPE1")
        log.debug(f"Setting artist: {artist}")
        audio.add(TPE1(encoding=3, text=artist))
    else:
        audio["title"] = title
        log.debug(f"Set title: {title}")
        audio["artist"] = artist
        log.debug(f"Set artist: {artist}")
    if cover_data:
        log.debug("Adding cover image")
        if use_id3:
            audio.delall("APIC")
            audio.add(APIC(encoding=3, mime="image/jpeg",
                      type=3, desc="Cover", data=cover_data))
    audio.save(v2_version=3)
    log.info(f"Metadata updated for {file_path}")


def split_audio_file(input_file, output_folder, duration, skip_chunk, start_offset=0):
    """
    Splits an audio file using ffmpeg. 
    Added start_offset (in milliseconds) to begin extraction after a given offset.
    """
    # Convert ms to seconds for ffmpeg.
    start_sec = start_offset / 1000.0
    duration_sec = duration / 1000.0
    # Construct the output fragment file name (you may loop or generate multiple fragments).
    output_file = f"{output_folder}/chunk_0.mp3"
    ffmpeg_cmd = [
        "ffmpeg",
        "-ss", str(start_sec),           # start offset
        "-i", input_file,
        "-t", str(duration_sec),         # duration to extract
        "-c", "copy",
        output_file,
        "-y"
    ]
    subprocess.run(ffmpeg_cmd, check=True)
