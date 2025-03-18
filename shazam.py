import asyncio
import math
import os
import re
import time
import shutil

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2, TPE1
from shazamio import Shazam
from pydub import AudioSegment
import convert_m4a
import logger  # new import

log = logger.logger  # use the shared logger

shazam = Shazam()

# Use fixed folder paths from volume mounts
path_to_dir = "/app/to_process"
processed_folder = "/app/processed_songs"
if not os.path.exists(processed_folder):
    os.makedirs(processed_folder)

music_segment_duration = 30000  # milliseconds
check_delay = 1  # seconds
output_file = "./songs.txt"
skip_chunk = 2  # 1 - every, 2 - odd ...

# for sort chunks


def try_int(s):
    try:
        return int(s)
    except:
        return s


def alphanum_key(s):
    return [try_int(c) for c in re.split("([0-9]+)", s)]


def update_mp3_metadata(file_path, title, artist):
    log.debug(f"Updating metadata for file {file_path}")
    try:
        audio = EasyID3(file_path)
    except Exception:
        log.debug("No existing EasyID3 tag found, creating new ID3 tag")
        audio = ID3(file_path)
        audio.add(TIT2(encoding=3, text=title))
        audio.add(TPE1(encoding=3, text=artist))
        audio.save(v2_version=3)
        log.info(f"Metadata added for {file_path} (new tag)")
        return
    audio["title"] = title
    audio["artist"] = artist
    audio.save()
    log.info(f"Metadata updated for {file_path}")


def split_audio_file(input_file_path, output_folder_path):
    audio = AudioSegment.from_file(input_file_path, format="mp3")
    chunk_length_ms = music_segment_duration

    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    log.info(
        f"{math.ceil(len(audio) / chunk_length_ms / skip_chunk)} fragments (length: {len(audio)})")
    log.info("Create...")
    log.info(f"Splitting file {input_file_path} into fragments...")
    for i, chunk_start in enumerate(range(0, len(audio), chunk_length_ms)):
        if i % skip_chunk == 0:
            chunk = audio[chunk_start: chunk_start + chunk_length_ms]
            output_file_path = os.path.join(
                output_folder_path, f"chunk_{i}.mp3")
            chunk.export(output_file_path, format="mp3")
            log.debug(f"Exported chunk_{i}.mp3 at {output_file_path}")


async def recognize(chunk_path, original_file):
    log.debug(f"Recognizing chunk: {chunk_path}")
    out = await shazam.recognize(chunk_path)
    if "track" in out:
        title = out["track"]["title"]
        artist = out["track"]["subtitle"]  # assuming subtitle is the artist
        log.debug(
            f"Track detected: {artist} - {title} for file {original_file}")
        update_mp3_metadata(original_file, title, artist)
        with open(output_file, "a+") as write_file:
            current_song = f"{artist} - {title}"
            # Check for duplicates (this assumes one song per line)
            write_file.seek(0)
            if any(current_song == x.rstrip("\r\n") for x in write_file):
                log.info(f"Duplicate song found: {current_song}")
            else:
                log.info(f"New song discovered: {current_song}")
                write_file.write(current_song + "\n")
        return True
    else:
        log.debug(f"No track identified in chunk: {chunk_path}")
    return False


async def main():
    log.info("Main processing started")
    files = [f for f in os.listdir(path_to_dir)
             if os.path.isfile(os.path.join(path_to_dir, f))]
    log.debug(f"Found {len(files)} files in {path_to_dir}")
    for file in files:
        log.debug(f"Processing file: {file}")
        # Only process mp3 and m4a files, ignore unsupported formats
        if not (file.lower().endswith('.mp3') or file.lower().endswith('.m4a')):
            log.info(f"Ignoring unsupported file format: {file}")
            continue

        original_file_path = os.path.join(path_to_dir, file)
        # If the file is m4a, convert to mp3
        if file.lower().endswith('.m4a'):
            log.info(f"Detected m4a file: {file}. Converting to mp3...")
            mp3_file = convert_m4a.convert_m4a_to_mp3(
                original_file_path, output_dir=path_to_dir)
            log.debug(f"Conversion complete: {mp3_file}")
            # Optionally remove the original m4a file
            os.remove(original_file_path)
            file = os.path.basename(mp3_file)
            original_file_path = mp3_file

        split_folder = file.split(".")[0]
        path_to_split_folder = os.path.join(path_to_dir, split_folder)
        log.debug(f"Splitting file {file} into folder: {path_to_split_folder}")
        split_audio_file(original_file_path, path_to_split_folder)
        split_files = [f for f in os.listdir(path_to_split_folder)
                       if os.path.isfile(os.path.join(path_to_split_folder, f))]
        split_files = sorted(split_files, key=alphanum_key)
        log.info(f"Starting recognition for file {file}")
        recognized_success = False
        for split_file in split_files:
            time.sleep(check_delay)
            log.debug(f"Processing chunk: {split_file}")
            recognized = await recognize(os.path.join(path_to_split_folder, split_file), original_file_path)
            if recognized:
                recognized_success = True
                log.info(f"Recognition succeeded on chunk {split_file}")
                break
        log.info(f"Deleting split folder: {path_to_split_folder}")
        shutil.rmtree(path_to_split_folder, ignore_errors=True)
        if recognized_success:
            dest_path = os.path.join(processed_folder, file)
            log.info(f"Moving file from {original_file_path} to {dest_path}")
            shutil.move(original_file_path, dest_path)
        else:
            log.info(
                f"File {file} was not successfully recognized. Leaving it in {path_to_dir}.")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
