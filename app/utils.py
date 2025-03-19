import math
import os
import re
import shutil
import requests  # added import for downloading cover image
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


def split_audio_file(input_file_path, output_folder_path, music_segment_duration, skip_chunk):
    log.debug(f"Splitting audio file {input_file_path}")
    audio = AudioSegment.from_file(input_file_path, format="mp3")
    chunk_length_ms = music_segment_duration

    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    total_fragments = math.ceil(len(audio) / chunk_length_ms / skip_chunk)
    log.info(
        f"{total_fragments} fragments to be created (audio length: {len(audio)} ms)")
    log.debug(f"Beginning splitting of file: {input_file_path}")
    for i, chunk_start in enumerate(range(0, len(audio), chunk_length_ms)):
        if i % skip_chunk == 0:
            chunk = audio[chunk_start: chunk_start + chunk_length_ms]
            output_file_path = os.path.join(
                output_folder_path, f"chunk_{i}.mp3")
            chunk.export(output_file_path, format="mp3")
            log.debug(f"Exported chunk_{i}.mp3 at {output_file_path}")
