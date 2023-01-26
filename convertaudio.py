"""
Tool to convert all audio files in a given folder via WAV into MP3 format

Usage:
    python3 convertaudio.py /path/to/folder

Afterwards all MP3 will be in /path/to/folder/converted_to_mp3/

The script is invoking Linux command line tools to do the actual work.
Different tools need to be installed for the different audio formats:
    - lame (encoding to MP3)
    - opusdec (decoding Opus audio)
    - oggdec (decoding Ogg Vorbis audio)
    - ffmpeg (decoding MP4 / aac audio)
"""
import os
from os.path import join, getsize
import shutil
import subprocess
import sys
import argparse

def convert_to_mp3(temp_file: str, output_file) -> bool:
    """
    temp_file is expected to be a WAV file and will be deleted after successfull encoding into MP3 file
    Returns True on success
    """
    # -h is even higher quality but takes longer
    # -b 128 is necessary, otherwise he's encoding mono 44100 Hz files only with 64kbs
    # and mono 16000 Hz only with 24kbs and sound quality is bad
    result = subprocess.run(['lame', '-h', '-b', '128', temp_file, output_file], capture_output=True, text=True)
    if result.returncode == 0:
        os.remove(temp_file)
        print(f"Successfully saved {output_file}")
        return True
    else:
        print(f"Error while trying to encode {temp_file} to MP3: {result.stdout}{result.stderr}")
        return False

def convert_audio(input_file: str, output_file: str):
    #print(f"TODO: Converting {input_file} to {output_file}")
    audio_type = subprocess.run(['file', '-b', input_file], capture_output=True, text=True).stdout
    temp_file = output_file + ".temp.wav"
    if audio_type.startswith('Ogg data, Opus audio'):
        result = subprocess.run(['opusdec', input_file, temp_file], capture_output=True, text=True)
        if result.returncode == 0:
            convert_to_mp3(temp_file, output_file)
        else:
            print(f"Couldn't decode OPUS audio of {input_file}: {result.stdout}{result.stderr}")
    elif audio_type.startswith('Ogg data, Vorbis audio'):
        result = subprocess.run(['oggdec', input_file, '-o', temp_file], capture_output=True, text=True)
        if result.returncode == 0:
            convert_to_mp3(temp_file, output_file)
        else:
            print(f"Couldn't decode Ogg Vorbis audio of {input_file}: {result.stdout}{result.stderr}")
    elif audio_type.startswith('ISO Media, MPEG v4 system, 3GPP') or audio_type.startswith('MPEG ADTS, AAC') or \
         audio_type.startswith('ISO Media, Apple iTunes ALAC/AAC-LC') or \
         audio_type.startswith('ISO Media, MP4 v2'):    # video file but extracting audio works the same
        # -y to overwrite existing files (otherwise he's stopping and expects y/n)
        result = subprocess.run(['ffmpeg', '-y', '-i', input_file, temp_file], capture_output=True, text=True)
        if result.returncode == 0:
            convert_to_mp3(temp_file, output_file)
        else:
            print(f"Couldn't decode MP4 audio of {input_file}: {result.stdout}{result.stderr}")
    elif audio_type.startswith('MPEG ADTS, layer III'):
        print(f"{input_file} is already in MP3 format: No converting necessary, copying into output folder.")
        shutil.copy(input_file, output_file)
    else:
        print(f"Couldn't identify audio type '{audio_type}' of {input_file}, skipping")

if __name__ == '__main__':
    msg = "Convert all audio files in a given folder to mp3"
    parser = argparse.ArgumentParser(prog="python3 convertaudio.py", description=msg)
    parser.add_argument("folder", help="Which folder to scan for audio files")
    args = parser.parse_args()
    folder = os.path.abspath(args.folder)
    mp3_folder = os.path.join(folder, 'converted_to_mp3')
    print(f"Converting all audios in {folder}: Saving MP3 files to {mp3_folder}")
    if not os.path.isdir(mp3_folder):
        os.makedirs(mp3_folder)
    with os.scandir(folder) as item:
        for entry in item:
            if not entry.name.startswith('.') and entry.is_file():
                base_name, extension = os.path.splitext(entry.name)
                if extension in ['.ogg', '.m4a', '.opus', '.aac', '.mp4']:
                    convert_audio(entry.path, os.path.join(mp3_folder, base_name + ".mp3"))
                else:
                    print(f"Skipping {entry.name}")
