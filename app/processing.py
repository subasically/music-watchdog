import os
import shutil
import asyncio
import logger as logger
import convert_m4a as convert_m4a
from utils import alphanum_key, split_audio_file
from recognize import recognize  # use the external recognize function

log = logger.logger


async def process_file(file, path_to_dir, processed_folder, music_segment_duration, skip_chunk, check_delay, output_file, shazam):
    log.debug(f"Starting processing for file: {file}")
    if not (file.lower().endswith('.mp3') or file.lower().endswith('.m4a')):
        log.info(f"Ignoring unsupported file format: {file}")
        return

    original_file_path = os.path.join(path_to_dir, file)
    if file.lower().endswith('.m4a'):
        log.info(f"Detected m4a file: {file}. Converting to mp3...")
        mp3_file = convert_m4a.convert_m4a_to_mp3(
            original_file_path, output_dir=path_to_dir)
        log.debug(f"Conversion complete: {mp3_file}")
        os.remove(original_file_path)
        file = os.path.basename(mp3_file)
        original_file_path = mp3_file

    split_folder = file.split(".")[0]
    path_to_split_folder = os.path.join(path_to_dir, split_folder)
    log.debug(f"Splitting file {file} into folder: {path_to_split_folder}")
    split_audio_file(original_file_path, path_to_split_folder,
                     music_segment_duration, skip_chunk)

    split_files = [f for f in os.listdir(path_to_split_folder)
                   if os.path.isfile(os.path.join(path_to_split_folder, f))]
    split_files = sorted(split_files, key=alphanum_key)
    log.info(f"Starting recognition for file: {file}")
    recognized_success = False
    for split_file in split_files:
        await asyncio.sleep(check_delay)
        log.debug(f"Processing chunk: {split_file}")
        recognized = await recognize(os.path.join(path_to_split_folder, split_file), original_file_path, output_file, shazam)
        if recognized:
            recognized_success = True
            log.info(
                f"Recognition succeeded on chunk: {split_file} for file: {file}")
            break
    log.debug(
        f"Finished processing chunks for file: {file}. Deleting split folder.")
    shutil.rmtree(path_to_split_folder, ignore_errors=True)
    if recognized_success:
        dest_path = os.path.join(processed_folder, file)
        log.info(f"Moving file from {original_file_path} to {dest_path}")
        shutil.move(original_file_path, dest_path)
    else:
        log.info(f"File {file} was not recognized. Left in {path_to_dir}.")
