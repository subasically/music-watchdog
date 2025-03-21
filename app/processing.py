import os
import shutil
import asyncio
import logger as logger
import convert_m4a
from utils import alphanum_key, split_audio_file
from recognize import recognize
from sftp_upload import upload_file_sftp
import unicodedata

log = logger.logger


def sanitize_filename(filename):
    """
    Normalize the filename to remove most special characters.
    This returns only ASCII characters.
    """
    # Normalize the string to NFKD form.
    normalized = unicodedata.normalize("NFKD", filename)
    # Encode to ASCII bytes, ignoring characters that can’t be encoded,
    # then decode back to string.
    ascii_filename = normalized.encode("ASCII", "ignore").decode("ASCII")
    # Optionally replace spaces or undesired characters.
    ascii_filename = ascii_filename.replace(" ", "_")
    return ascii_filename


async def handle_conversion(file, path_to_dir):
    """
    Convert m4a files to mp3. Return the file name and its path.
    """
    original_file_path = os.path.join(path_to_dir, file)
    if file.lower().endswith('.m4a'):
        log.info(f"Converting m4a file: {file}")
        mp3_file = convert_m4a.convert_m4a_to_mp3(
            original_file_path, output_dir=path_to_dir)
        log.debug(f"Conversion complete: {mp3_file}")
        os.remove(original_file_path)
        file = os.path.basename(mp3_file)
        original_file_path = mp3_file
    return file, original_file_path


def prepare_split_folder(file, path_to_dir):
    """
    Prepare a folder for split audio chunks.
    """
    split_folder = file.split(".")[0]
    path_to_split_folder = os.path.join(path_to_dir, split_folder)
    if not os.path.exists(path_to_split_folder):
        # Create the split folder if it doesn't exist
        log.debug(f"Creating split folder: {path_to_split_folder}")
        os.makedirs(path_to_split_folder, mode=0o777, exist_ok=True)
    return path_to_split_folder


async def process_chunks(file, original_file_path, path_to_split_folder, music_segment_duration, skip_chunk, check_delay, output_file, shazam):
    """
    Split the audio file into chunks and try to recognize the song on each chunk.
    The split_audio_file function is now passed a start_offset (in ms) to choose a segment beyond the beginning.
    """
    # Set the desired start offset to 45 seconds (45000 milliseconds)
    segment_offset = 45000

    log.debug(
        f"Splitting file {file} into folder: {path_to_split_folder} starting at offset {segment_offset} ms")
    # Update the split_audio_file to accept a start_offset parameter.
    split_audio_file(original_file_path, path_to_split_folder,
                     music_segment_duration, skip_chunk, start_offset=segment_offset)
    split_files = [f for f in os.listdir(path_to_split_folder)
                   if os.path.isfile(os.path.join(path_to_split_folder, f))]
    split_files = sorted(split_files, key=alphanum_key)
    log.info(f"Starting recognition for file: {file}")

    recognized_success = False
    for split_file in split_files:
        await asyncio.sleep(check_delay)
        chunk_path = os.path.join(path_to_split_folder, split_file)
        log.debug(f"Processing chunk: {split_file}")
        recognized = await recognize(chunk_path, original_file_path, output_file, shazam)
        if recognized:
            recognized_success = True
            log.info(
                f"Recognition succeeded on chunk: {split_file} for file: {file}")
            break
    # Clean up split folder
    shutil.rmtree(path_to_split_folder, ignore_errors=True)
    return recognized_success


def move_file(original_file_path, file, path_to_dir, processed_folder, recognized_success):
    """
    Move the processed file to the correct folder after sanitizing its filename.
    """
    if recognized_success:
        dest_folder = processed_folder
    else:
        dest_folder = os.path.join(path_to_dir, "unrecognized")
        if not os.path.exists(dest_folder):
            log.debug(f"Creating unrecognized folder: {dest_folder}")
            os.makedirs(dest_folder, mode=0o777, exist_ok=True)

    # Sanitize the filename to remove or replace special characters.
    safe_filename = sanitize_filename(file)
    dest_path = os.path.join(dest_folder, safe_filename)
    log.info(f"Moving file from {original_file_path} to {dest_path}")
    shutil.move(original_file_path, dest_path)
    return dest_path  # Return new path after moving


async def process_file(file, path_to_dir, processed_folder, music_segment_duration, skip_chunk, check_delay, output_file, shazam):
    """
    Coordinator: convert (if needed), split the audio,
    recognize song chunks, move the file, and then attempt SFTP upload.
    """
    log.debug(f"Starting processing for file: {file}")

    if not (file.lower().endswith('.mp3') or file.lower().endswith('.m4a')):
        log.info(f"Ignoring unsupported file format: {file}")
        return

    # Handle file conversion
    file, original_file_path = await handle_conversion(file, path_to_dir)

    # Prepare the folder for split chunks
    path_to_split_folder = prepare_split_folder(file, path_to_dir)

    # Process chunks and attempt recognition
    recognized_success = await process_chunks(file, original_file_path, path_to_split_folder,
                                              music_segment_duration, skip_chunk, check_delay, output_file, shazam)

    # Move the original file based on recognition outcome and get its new location.
    new_file_path = move_file(original_file_path, file,
                              path_to_dir, processed_folder, recognized_success)

    # If recognized successfully, attempt SFTP upload
    if recognized_success:
        # Retrieve SFTP credentials from environment variables.
        sftp_username = os.environ.get("SFTP_USERNAME")
        sftp_host = os.environ.get("SFTP_HOST")
        sftp_password = os.environ.get("SFTP_PASSWORD")
        sftp_port = int(os.environ.get("SFTP_PORT", "22"))
        sftp_remote_dir = os.environ.get("SFTP_REMOTE_DIR", "/upload")
        if sftp_username and sftp_host and sftp_password:
            upload_success = upload_file_sftp(
                new_file_path, sftp_username, sftp_host, sftp_password, sftp_port, sftp_remote_dir)
            if not upload_success:
                log.error(
                    f"SFTP upload failed for {new_file_path}. File remains in processed folder.")
        else:
            log.error("SFTP credentials not fully set. Skipping SFTP upload.")
    else:
        log.info(
            f"File {file} was not recognized. Moved to unrecognized folder.")
