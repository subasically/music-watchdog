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
    log.error(
        f"Input directory {path_to_dir} does not exist. Please create it manually.")
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
        # Check for files in the input folder.
        files = [f for f in os.listdir(path_to_dir)
                 if os.path.isfile(os.path.join(path_to_dir, f))]
        file_count = len(files)
        log.info(f"Found {file_count} files in {path_to_dir}")

        if file_count > 0:
            for file in files:
                send_slack_notification(f"Processing file: {file}")
                await processing.process_file(file, path_to_dir, processed_folder,
                                              music_segment_duration, skip_chunk,
                                              check_delay, output_file, shazam)
        else:
            log.info("No new files to process.")
            # Check if there are files in the processed folder pending upload.
            processed_files = [f for f in os.listdir(processed_folder)
                               if os.path.isfile(os.path.join(processed_folder, f))]
            if processed_files:
                for file in processed_files:
                    log.info(f"Found processed file pending upload: {file}")
                    file_path = os.path.join(processed_folder, file)
                    # Retrieve SFTP credentials from environment.
                    sftp_username = os.environ.get("SFTP_USERNAME")
                    sftp_host = os.environ.get("SFTP_HOST")
                    sftp_password = os.environ.get("SFTP_PASSWORD")
                    sftp_port = int(os.environ.get("SFTP_PORT", 2022))
                    sftp_remote_dir = os.environ.get(
                        "SFTP_REMOTE_DIR", "/upload")
                    if sftp_username and sftp_host and sftp_password:
                        upload_success = processing.upload_file_sftp(
                            file_path, sftp_username, sftp_host, sftp_password, sftp_port, sftp_remote_dir)
                        if not upload_success:
                            log.error(
                                f"SFTP upload failed for {file_path}. File remains in processed folder.")
                    else:
                        log.error(
                            "SFTP credentials not fully set. Skipping SFTP upload.")
            else:
                log.info("No processed files pending upload.")

        log.info(f"Sleeping for {sleep_time_minutes} minutes.")
        await asyncio.sleep(sleep_time_seconds)

asyncio.run(main())


asyncio.run(main())
