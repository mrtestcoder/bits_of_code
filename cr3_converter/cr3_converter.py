import argparse
import os
import rawpy
import imageio
from pathlib import Path
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

def convert_image(args):
    """
    Converts a single CR3 image to a specified format.

    Args:
        args (tuple): A tuple containing the source file path, destination folder, and output extension.
    """
    source_file, dest_folder, out_ext = args
    try:
        with rawpy.imread(str(source_file)) as raw:
            rgb = raw.postprocess()
            dest_file = dest_folder / f"{source_file.stem}.{out_ext}"
            imageio.imwrite(str(dest_file), rgb)
            return source_file, None
    except Exception as e:
        return source_file, e

def main():
    """
    Main function to handle command-line arguments and initiate the conversion process.
    """
    parser = argparse.ArgumentParser(description="Convert CR3 raw images to other formats.")
    parser.add_argument("source_folder", type=str, help="Source folder containing CR3 files.")
    parser.add_argument("dest_folder", type=str, help="Destination folder for converted files.")
    parser.add_argument("--ext", type=str, default="jpg", help="Output file extension (e.g., jpg, png, tiff).")
    parser.add_argument("--workers", type=int, default=cpu_count(), help="Number of worker processes to use.")
    args = parser.parse_args()

    source_folder = Path(args.source_folder)
    dest_folder = Path(args.dest_folder)
    out_ext = args.ext.lower()

    if not source_folder.is_dir():
        print(f"Error: Source folder '{source_folder}' not found.")
        return

    dest_folder.mkdir(parents=True, exist_ok=True)

    cr3_files = list(source_folder.glob("*.cr3"))
    if not cr3_files:
        print(f"No CR3 files found in '{source_folder}'.")
        return

    print(f"Found {len(cr3_files)} CR3 files to convert.")
    print(f"Using {args.workers} worker processes.")

    conversion_args = [(file, dest_folder, out_ext) for file in cr3_files]

    with Pool(processes=args.workers) as pool:
        with tqdm(total=len(cr3_files), desc="Converting images") as pbar:
            for source_file, error in pool.imap_unordered(convert_image, conversion_args):
                if error:
                    print(f"Failed to convert {source_file.name}: {error}")
                pbar.update()

    print("Conversion complete.")

if __name__ == "__main__":
    main()
