import os
import json
import paramiko
import logger as logger
from notifier import send_slack_notification

log = logger.logger

TRACKER_JSON = os.path.join(os.path.dirname(
    __file__), "..", "uploaded_files.json")


def load_tracker():
    if os.path.exists(TRACKER_JSON):
        with open(TRACKER_JSON, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}


def save_tracker(data):
    with open(TRACKER_JSON, "w") as f:
        json.dump(data, f)


def upload_file_sftp(file_path, username, host, password, port, remote_directory):
    """
    Connect to the SFTP server and upload a single file.
    If upload is successful, add the file (by its basename) to the tracker.
    """
    port = int(port)
    tracker = load_tracker()
    basename = os.path.basename(file_path)
    if basename in tracker:
        log.info(f"File {basename} already uploaded. Skipping SFTP upload.")
        return True

    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # Ensure remote directory exists.
        try:
            sftp.chdir(remote_directory)
        except IOError:
            sftp.mkdir(remote_directory)
            sftp.chdir(remote_directory)

        remote_path = os.path.join(remote_directory, basename)
        log.info(f"Uploading {file_path} to {remote_path}")
        sftp.put(file_path, remote_path)
        sftp.close()
        transport.close()

        # Update tracker and delete the local file.
        tracker[basename] = True
        save_tracker(tracker)
        log.info(f"Upload succeeded for {basename}. Deleting local file.")
        os.remove(file_path)
        send_slack_notification(
            f"Uploaded and deleted {basename} from processed files.")
        return True
    except Exception as e:
        log.error(f"SFTP upload failed for {basename}: {e}")
        send_slack_notification(f"SFTP upload failed for {basename}: {e}")
        return False


if __name__ == "__main__":
    # For testing, retrieve credentials from env vars.
    sftp_username = os.environ.get("SFTP_USERNAME")
    sftp_host = os.environ.get("SFTP_HOST")
    sftp_password = os.environ.get("SFTP_PASSWORD")
    sftp_port = os.environ.get("SFTP_PORT", "22")
    sftp_remote_dir = os.environ.get("SFTP_REMOTE_DIR", "/upload")

    # Example file path—adjust as needed.
    test_file = os.path.join(os.path.dirname(
        __file__), "..", "processed_songs", "example.mp3")
    if not (sftp_username and sftp_host and sftp_password):
        log.error("SFTP credentials not set in environment.")
    else:
        upload_file_sftp(test_file, sftp_username, sftp_host,
                         sftp_password, sftp_port, sftp_remote_dir)
