#!/usr/bin/env python3

import os
import random
import subprocess
import argparse
from tempfile import mkdtemp

def find_wav_files(directory, ext='.wav'):
    """Recursively find all .wav files in the given directory."""
    if not os.path.isdir(directory):
        raise ValueError(f"{directory} is not a directory")
    wav_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(ext):
                wav_files.append(os.path.join(root, file))
    return wav_files

def get_sample_rate(file_path):
    """Get the sample rate of a WAV file using soxi."""
    result = subprocess.run(['soxi', '-r', file_path], capture_output=True, text=True)
    return int(result.stdout.strip())

def resample_wav_file(input_file, output_file, target_sample_rate):
    """Resample a WAV file to a specific sample rate using sox."""
    subprocess.run(['sox', input_file, '-r', str(target_sample_rate), output_file], check=True)

def process_files(files, target_sample_rate, temp_dir):
    """Process files to ensure they have the target sample rate, using temporary resampling if necessary."""
    processed_files = []
    for file in files:
        if get_sample_rate(file) != target_sample_rate:
            # Need to resample
            temp_file = os.path.join(temp_dir, os.path.basename(file))
            resample_wav_file(file, temp_file, target_sample_rate)
            processed_files.append(temp_file)
        else:
            # File is already at the correct sample rate
            processed_files.append(file)
    return processed_files

def merge_wav_files(files, output_file):
    """Merge wav files into a single file using sox."""
    command = ['sox'] + files + [output_file]
    subprocess.run(command, check=True)


def main(input_directory, output_directory, target_sample_rate, randomize=False, batch_size=250, ext='.wav'):
    wav_files = find_wav_files(input_directory, ext=ext)
    file_counter = 1
    temp_dir = mkdtemp()  # Create a temporary directory for resampled files

    if randomize:
        random.shuffle(wav_files)

    for i in range(0, len(wav_files), batch_size):
        batch_files = wav_files[i:i+batch_size]
        processed_files = process_files(batch_files, target_sample_rate, temp_dir)
        output_file = os.path.join(output_directory, f"sample{file_counter}.wav")
        merge_wav_files(processed_files, output_file)
        print(f"Merged {len(processed_files)} files into {output_file}")
        file_counter += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge WAV files in batches of 250 using SoX.")
    parser.add_argument("input_directory", type=str, help="The directory containing WAV files to merge.")
    parser.add_argument("output_directory", type=str, help="The directory where merged WAV files will be saved.")
    parser.add_argument("--randomize", action="store_true", help="Randomize the order of input files.")
    parser.add_argument("--rate", type=int, default=22050, help="Target sample rate for all files.")
    parser.add_argument("--batch-size", type=int, default=250, help="Target sample rate for all files.")
    parser.add_argument("--ext", type=str, default='.wav', help="Source extension.")

    args = parser.parse_args()

    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    main(args.input_directory, args.output_directory, args.rate, args.randomize, args.batch_size, args.ext)

