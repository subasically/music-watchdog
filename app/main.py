from shazamio import Shazam
import processing as processing
import logger as logger
import asyncio
import sys
import os
from notifier import send_slack_notification
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

log = logger.logger
shazam = Shazam()

# Use fixed folder paths from volume mounts (changed processed_folder to a relative path)
path_to_dir = "/app/to_process"
processed_folder = "/app/processed_songs"
if not os.path.exists(path_to_dir):
    # Ensure input directory exists
    log.info(
        f"Input directory {path_to_dir} does not exist. Creating it.")
    os.makedirs(path_to_dir, mode=0o777, exist_ok=True)
if not os.path.exists(processed_folder):
    # Ensure processed directory exists
    log.info(
        f"Processed directory {processed_folder} does not exist. Creating it.")
    os.makedirs(processed_folder, mode=0o777, exist_ok=True)

music_segment_duration = 30000  # milliseconds
check_delay = 1  # seconds
output_file = "./songs.txt"
skip_chunk = 2  # 1 - every, 2 - odd ...

sleep_time_minutes = int(os.getenv("SLEEP_TIME_MINUTES", "5"))
sleep_time_seconds = sleep_time_minutes * 60


async def main():
    log.info("Starting Music Watchdog")

    send_slack_notification("Music Watchdog is running")

    while True:
        files = [f for f in os.listdir(path_to_dir) if os.path.isfile(
            os.path.join(path_to_dir, f))]
        file_count = len(files)
        log.info(f"Found {file_count} files in {path_to_dir}")
        if file_count == 0:
            for remaining in range(sleep_time_minutes, 0, -1):
                log.info(
                    f"Sleeping for {remaining} minute{'s' if remaining != 1 else ''}.")
                await asyncio.sleep(60)
            continue
        for file in files:
            send_slack_notification(f"Processing file: {file}")
            await processing.process_file(file, path_to_dir, processed_folder,
                                          music_segment_duration, skip_chunk,
                                          check_delay, output_file, shazam)
        log.debug("Waiting 1 second before next processing cycle.")
        await asyncio.sleep(1)


asyncio.run(main())
