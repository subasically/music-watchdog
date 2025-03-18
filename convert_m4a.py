import os
from pydub import AudioSegment


def convert_m4a_to_mp3(m4a_file, output_dir=None):
    """
    Convert an m4a file to mp3.
    Returns the path to the new mp3 file.
    """
    if output_dir is None:
        output_dir = os.path.dirname(m4a_file)
    base = os.path.splitext(os.path.basename(m4a_file))[0]
    mp3_file = os.path.join(output_dir, base + ".mp3")
    print(f"Converting {m4a_file} -> {mp3_file}")
    audio = AudioSegment.from_file(m4a_file, format="m4a")
    audio.export(mp3_file, format="mp3")
    return mp3_file


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python convert_m4a.py <file.m4a>")
        sys.exit(1)
    m4a_file = sys.argv[1]
    mp3_file = convert_m4a_to_mp3(m4a_file)
    print(f"Converted file saved to: {mp3_file}")
