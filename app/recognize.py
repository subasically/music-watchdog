import os
import difflib
import logger as logger
from utils import update_mp3_metadata
from notifier import send_slack_notification

log = logger.logger


def is_match(recognized_artist, recognized_title, file_name, threshold=0.7):
    """
    Validate recognized track info by comparing with the filename.
    Expected file_name format: "ARTIST - TITLE.mp3"
    Returns True if both artist and title comparisons meet the threshold.
    """
    base = os.path.splitext(os.path.basename(file_name))[0]
    try:
        file_artist, file_title = [x.strip().lower()
                                   for x in base.split('-', 1)]
    except ValueError:
        log.debug(
            f"Filename {file_name} is not in the expected 'ARTIST - TITLE' format.")
        return False

    artist_ratio = difflib.SequenceMatcher(
        None, recognized_artist.lower(), file_artist).ratio()
    title_ratio = difflib.SequenceMatcher(
        None, recognized_title.lower(), file_title).ratio()
    log.debug(
        f"Comparing with file name: artist_ratio={artist_ratio:.2f}, title_ratio={title_ratio:.2f}")
    return artist_ratio >= threshold and title_ratio >= threshold


async def recognize(chunk_path, original_file, output_file, shazam):
    log.debug(f"Recognizing chunk: {chunk_path}")
    out = await shazam.recognize(chunk_path)
    log.debug(f"Recognition result: {out}")

    if "track" in out:
        track_data = out["track"]
        recognized_artist = track_data.get("subtitle", "")
        recognized_title = track_data.get("title", "")
        log.debug(
            f"Track detected: {recognized_artist} - {recognized_title} for file: {original_file}")

        # Send slack notification
        send_slack_notification(
            f"Recognized: {recognized_artist} - {recognized_title}")

        # Validate recognition by comparing with the local file name.
        if not is_match(recognized_artist, recognized_title, original_file):
            log.debug(
                f"Validation failed: Recognized info does not sufficiently match the file name for {original_file}")
            return False

        update_mp3_metadata(original_file, track_data=track_data)
        with open(output_file, "a+") as write_file:
            current_song = f"{recognized_artist} - {recognized_title}"
            write_file.seek(0)
            if any(current_song == x.strip() for x in write_file):
                log.info(f"Duplicate song found: {current_song}")
            else:
                log.info(f"New song discovered: {current_song}")
                write_file.write(current_song + "\n")
        return True
    else:
        log.debug(f"No track identified in chunk: {chunk_path}")
    return False
