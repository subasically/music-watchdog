# Music Watchdog

Music Watchdog is a Python-based application that monitors a designated folder for new music files, processes them using the Shazam API to identify songs, and updates the mp3 metadata accordingly. It also converts m4a files to mp3 before processing and can be extended to upload processed files via SFTP.

## Features

- **Song Recognition:**  
  Uses [Shazamio](https://github.com/MarioVilas/shazamio) to identify tracks from audio snippets.

- **Metadata Updates:**  
  Updates ID3 tags in mp3 files with the recognized song title and artist.

- **Format Conversion:**  
  Automatically converts m4a files to mp3 so that only mp3 files are processed.

- **Notifications:**  
  Sends notifications via Slack when processing starts and upon identifying new tracks.
  
- **(Planned) SFTP Upload:**  
  🚧 SFTP upload of processed files to Azuracast is planned as a future enhancement.

## Prerequisites

- [Python 3.12](https://www.python.org/downloads/)
- [ffmpeg](https://ffmpeg.org/) – required by [pydub](https://github.com/jiaaro/pydub)
- Docker (optional) if you wish to run the application via containers
- Environment variables for SFTP and Slack notifications as needed

## Getting Started

### Running Locally

1. **Clone the repository** and install dependencies:
   ```bash
   git clone <repository_url>
   cd music-watchdog
   pip install -r requirements.txt
   ```

2. **Set Environment Variables:**  
   Create a `.env` file or set environment variables in your shell:
   - `DEBUG` – Set to `true` to enable verbose logging.
   - `SLACK_WEBHOOK_URL` – Your Slack webhook URL.
   - *(For future SFTP integration):*  
     - `SFTP_USERNAME`
     - `SFTP_HOST`
     - `SFTP_PASSWORD`
     - `SFTP_PORT`
     - `SFTP_REMOTE_DIR`
     - `SFTP_LOCAL_DIR`

3. **Prepare Folders:**  
   Ensure that the folders where music files will be placed exist:
   - Input folder: `/app/to_process` (or as defined by your volume mounts)
   - Output folder: `/app/processed_songs`

4. **Run the Application:**  
   Simply call:
   ```bash
   python app/main.py
   ```

### Running with Docker

Use the provided `Dockerfile` and `docker-compose.yml` for containerization.

1. **Build the Docker Image:**
   ```bash
   docker-compose build
   ```

2. **Run the Container:**
   ```bash
   docker-compose up -d
   ```

3. **Directory Mounts:**  
   The `docker-compose.yml` file mounts host directories to:
   - `/app/to_process`: Folder to drop new files (mp3 or m4a)
   - `/app/processed_songs`: Folder for processed songs

## Application Workflow

1. The application continuously monitors `/app/to_process` for incoming files.
2. If a file is in `.m4a` format, it is converted to `.mp3` before being processed.
3. The mp3 file is split into segments, then recognized using the Shazam API.
4. On a successful recognition, the mp3 metadata is updated with the track information.
5. Processed files are moved to `/app/processed_songs`.
6. Slack notifications are sent to indicate processing progress.

## Future Enhancements

- ⬜️ **Album Artwork Extraction:**  
  Retrieve album artwork and embed it in the mp3 metadata.

- 🚧 **SFTP Upload:**  
  Integrate SFTP uploads to Azuracast for automatically moving processed files to a remote server.

- ✅ **Slack Notifications:**  
  Already implemented to alert on significant processing steps.

## Troubleshooting & Logging

- **Logging:**  
  The application uses a custom logger that outputs debug messages to stdout and a log file (`music_watchdog.log`) when `DEBUG` is set to `true`.

- **File Formats:**  
  Only `.mp3` and `.m4a` files are processed. Other formats are ignored.

- **Volumes & Paths:**  
  Make sure your Docker volume mounts align with the paths defined in the code (`/app/to_process` and `/app/processed_songs`).

## License

[MIT License](LICENSE)

## Acknowledgments

- Shazam API and [Shazamio](https://github.com/MarioVilas/shazamio)
- [Pydub](https://github.com/jiaaro/pydub) for audio processing
- [Paramiko](http://www.paramiko.org/) for SFTP functionality