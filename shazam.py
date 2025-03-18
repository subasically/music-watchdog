import asyncio
import math
import os
import re
import time

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2, TPE1

from shazamio import Shazam
from pydub import AudioSegment
import shutil

shazam = Shazam()

path_to_dir = os.environ.get("PATH_TO_DIR")
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
    print(f"Update metadata: {title} - {artist} for {file_path}")

    try:
        audio = EasyID3(file_path)
    except Exception:
        # If no ID3 tag exists, create one using ID3
        audio = ID3(file_path)
        audio.add(TIT2(encoding=3, text=title))
        audio.add(TPE1(encoding=3, text=artist))
        audio.save(v2_version=3)
        return
    # Update the tags
    audio["title"] = title
    audio["artist"] = artist
    audio.save()


def split_audio_file(input_file_path, output_folder_path):
    audio = AudioSegment.from_file(input_file_path, format="mp3")
    chunk_length_ms = music_segment_duration

    # Split the audio file into chunks of length 30 seconds
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    print(
        f"{math.ceil(len(audio) / chunk_length_ms / skip_chunk)} fragments (length: {len(audio)})"
    )
    print("Create...")
    for i, chunk_start in enumerate(range(0, len(audio), chunk_length_ms)):
        if i % skip_chunk == 0:
            chunk = audio[chunk_start: chunk_start + chunk_length_ms]

            # Save the chunk to a file
            output_file_path = os.path.join(
                output_folder_path, f"chunk_{i}.mp3")
            chunk.export(output_file_path, format="mp3")


async def recognize(chunk_path, original_file):
    out = await shazam.recognize(chunk_path)
    if "track" in out:
        title = out["track"]["title"]
        artist = out["track"]["subtitle"]  # assuming subtitle is the artist

        # Update the actual song's metadata (original file)
        update_mp3_metadata(original_file, title, artist)

        with open(output_file, "r+") as write_file:
            current_song = f"{artist} - {title}"
            if any(current_song == x.rstrip("\r\n") for x in write_file):
                print(f"Duplicate ({current_song})")
            else:
                print(f"New song: {current_song}")
                write_file.write(current_song + "\n")
        return True  # Return True when recognition is successful
    else:
        print("Undefined segment :(")
    return False


async def main():
    if not path_to_dir:
        print("PATH_TO_DIR not set")
        return

    print("Start...")
    files = [
        f
        for f in os.listdir(path_to_dir)
        if os.path.isfile(os.path.join(path_to_dir, f))
    ]
    for file in files:
        original_file_path = os.path.join(path_to_dir, file)
        split_folder = file.split(".")[0]
        path_to_split_folder = os.path.join(path_to_dir, split_folder)
        split_audio_file(original_file_path, path_to_split_folder)
        split_files = [
            f
            for f in os.listdir(path_to_split_folder)
            if os.path.isfile(os.path.join(path_to_split_folder, f))
        ]
        split_files = sorted(split_files, key=alphanum_key)
        print("Recognize...")
        # Process each chunk until recognition is successful
        for split_file in split_files:
            time.sleep(check_delay)
            recognized = await recognize(
                os.path.join(path_to_split_folder,
                             split_file), original_file_path
            )
            if recognized:
                # Stop checking remaining fragments after successful recognition
                break
        print("Deleting:", path_to_split_folder)
        shutil.rmtree(path_to_split_folder, ignore_errors=True)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
