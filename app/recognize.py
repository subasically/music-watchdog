import logger as logger
from utils import update_mp3_metadata

log = logger.logger


async def recognize(chunk_path, original_file, output_file, shazam):
    log.debug(f"Recognizing chunk: {chunk_path}")
    out = await shazam.recognize(chunk_path)
    log.debug(f"Recognition result: {out}")

    if "track" in out:
        track_data = out["track"]
        log.debug(
            f"Track detected: {track_data.get('subtitle')} - {track_data.get('title')} for file: {original_file}")
        update_mp3_metadata(original_file, track_data=track_data)
        with open(output_file, "a+") as write_file:
            current_song = f"{track_data.get('subtitle')} - {track_data.get('title')}"
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
