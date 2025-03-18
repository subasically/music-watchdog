import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from mutagen import File
from mutagen.id3 import ID3, APIC, error as ID3Error
import requests
import paramiko
import logging

# Placeholder function to fetch album artwork (replace with your API integration)
def fetch_album_artwork(artist, title):
    # For now, return None or implement your own artwork lookup
    return None

def update_metadata(file_path):
    try:
        audio = File(file_path, easy=True)
        if audio is None:
            logging.error("Unsupported file format: %s", file_path)
            return False

        # Assume filename format "Artist - Title.mp3"
        filename = os.path.basename(file_path)
        if ' - ' in filename:
            artist, title = filename.rsplit('.', 1)[0].split(' - ', 1)
        else:
            artist, title = "Unknown Artist", filename

        # Update metadata if missing
        if 'artist' not in audio or not audio['artist'][0]:
            audio['artist'] = [artist]
        if 'title' not in audio or not audio['title'][0]:
            audio['title'] = [title]

        audio.save()

        # For mp3 files, embed artwork using ID3 tags
        if file_path.lower().endswith('.mp3'):
            try:
                tags = ID3(file_path)
            except ID3Error:
                tags = ID3()

            artwork = fetch_album_artwork(artist, title)
            if artwork:
                tags['APIC'] = APIC(
                    encoding=3,  # utf-8
                    mime='image/jpeg',
                    type=3,      # cover (front)
                    desc='Cover',
                    data=artwork
                )
            tags.save(file_path)
        return True
    except Exception as e:
        logging.exception("Error updating metadata for %s", file_path)
        return False

def upload_to_azuracast(file_path, playlist):
    # SFTP connection settings
    sftp_host = "173.215.80.121"  # use this IP if needed, or change to radio.subasically.me
    sftp_port = 2022
    username = "watchdog"
    password = "M3d!n@201*"
    
    # Determine the remote directory based on the playlist.
    # Adjust this path if AzuraCast expects files in a different location.
    remote_dir = f"/uploads/{playlist}"
    
    try:
        # Set up the SFTP transport connection
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Create the remote directory if it doesn't exist
        try:
            sftp.chdir(remote_dir)
        except IOError:
            logging.info("Remote directory %s doesn't exist, creating it.", remote_dir)
            sftp.mkdir(remote_dir)
        
        # Determine remote file path
        remote_path = os.path.join(remote_dir, os.path.basename(file_path))
        
        # Upload the file
        sftp.put(file_path, remote_path)
        logging.info("Uploaded %s to %s", file_path, remote_path)
        
    except Exception as e:
        logging.exception("Error uploading file via SFTP: %s", e)
    finally:
        if 'sftp' in locals():
            sftp.close()
        if 'transport' in locals():
            transport.close()

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if (not event.is_directory and 
            (event.src_path.lower().endswith('.mp3') or event.src_path.lower().endswith('.m4a'))):
            logging.info("Detected new file: %s", event.src_path)
            time.sleep(5)  # wait to ensure file is fully written
            if update_metadata(event.src_path):
                # Assume the parent folder name indicates the playlist name
                playlist = os.path.basename(os.path.dirname(event.src_path))
                upload_to_azuracast(event.src_path, playlist)
            else:
                logging.error("Failed to process metadata for %s", event.src_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    watch_folder = "test_watch_folder"  # update this path
    observer = Observer()
    observer.schedule(FileHandler(), path=watch_folder, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
