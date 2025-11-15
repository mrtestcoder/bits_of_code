#!/usr/bin/env python3

import argparse
import os
import subprocess
import rawpy
from PIL import Image


def check_dependencies():
    """Check for required dependencies"""
    for dep in ["exiftool"]:
        if subprocess.call(["which", dep], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
            print(f"Error: {dep} not found. Please install it.")
            exit(1)
    try:
        import rawpy
        from PIL import Image
    except ImportError as e:
        print(f"Error: {e.name} not found. Please install it using pip.")
        exit(1)


def convert_cr3_to_tiff(filepath):
    """Convert a CR3 file to TIFF"""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return
    if not filepath.lower().endswith(".cr3"):
        print(f"Error: {filepath} is not a CR3 file.")
        return
    output_filepath = os.path.splitext(filepath)[0] + ".tiff"
    print(f"Converting {filepath} to {output_filepath}")
    with rawpy.imread(filepath) as raw:
        rgb = raw.postprocess()
        Image.fromarray(rgb).save(output_filepath, format="TIFF")

    # Copy EXIF data from CR3 to TIFF
    subprocess.call([
        "exiftool",
        "-tagsfromfile",
        filepath,
        "-overwrite_original",
        output_filepath
    ])


def convert_cr3_to_jpeg(filepath, quality):
    """Convert a CR3 file to JPEG"""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return
    if not filepath.lower().endswith(".cr3"):
        print(f"Error: {filepath} is not a CR3 file.")
        return
    output_filepath = os.path.splitext(filepath)[0] + ".jpeg"
    print(f"Converting {filepath} to {output_filepath} with quality {quality}%")
    with rawpy.imread(filepath) as raw:
        rgb = raw.postprocess()
        Image.fromarray(rgb).save(output_filepath, quality=quality, optimize=True)

    # Copy EXIF data from CR3 to JPEG
    subprocess.call([
        "exiftool",
        "-tagsfromfile",
        filepath,
        "-overwrite_original",
        output_filepath
    ])


def set_gps_coordinates(filepath, lat, lon):
    """Set GPS coordinates for a file"""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return
    print(f"Setting GPS coordinates for {filepath} to {lat}, {lon}")
    subprocess.call([
        "exiftool",
        "-overwrite_original",
        f"-GPSLatitude={lat}",
        f"-GPSLongitude={lon}",
        f"-GPSLatitudeRef={ 'N' if float(lat) >= 0 else 'S'}",
        f"-GPSLongitudeRef={ 'E' if float(lon) >= 0 else 'W'}",
        filepath
    ])


def get_args():
    """Get command line arguments"""
    parser = argparse.ArgumentParser(description="Edit image metadata")
    parser.add_argument("-f", "--files", nargs="+", help="List of files to process")
    parser.add_argument("-lat", "--latitude", type=float, help="Latitude")
    parser.add_argument("-lon", "--longitude", type=float, help="Longitude")
    parser.add_argument("-c", "--convert", choices=["jpeg", "tiff"], help="Convert to another format")
    parser.add_argument("-q", "--quality", type=int, default=100, help="JPEG quality (1-100)")
    return parser.parse_args()


def process_files(files, args):
    """Process a list of files"""
    for file in files:
        if not os.path.exists(file):
            print(f"Error: {file} not found.")
            continue
        if args.latitude and args.longitude:
            set_gps_coordinates(file, args.latitude, args.longitude)
        if args.convert == "jpeg" and file.lower().endswith(".cr3"):
            convert_cr3_to_jpeg(file, args.quality)
        elif args.convert == "tiff" and file.lower().endswith(".cr3"):
            convert_cr3_to_tiff(file)


def main():
    """Main function"""
    check_dependencies()
    args = get_args()
    if args.files:
        process_files(args.files, args)


if __name__ == "__main__":
    main()
