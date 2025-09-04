# CR3 Image Converter

This script converts Canon CR3 raw images to other formats like JPEG, PNG, or TIFF using multiprocessing to speed up the process.

## Features

-   Convert CR3 files to JPG, PNG, TIFF, etc.
-   Process multiple files in parallel using multiprocessing.
-   Command-line interface for specifying source and destination folders.
-   Progress bar to show the conversion progress.

## Installation

1.  **Clone the repository or download the script.**

2.  **Install the required Python libraries:**

    ```bash
    pip install rawpy imageio tqdm
    ```

## Usage

To use the script, run it from the command line with the source and destination folders as arguments.

```bash
python cr3_converter.py <source_folder> <destination_folder> [options]
```

### Arguments

-   `source_folder`: The path to the folder containing the `.cr3` files.
-   `destination_folder`: The path to the folder where the converted images will be saved.

### Options

-   `--ext <extension>`: The output file extension. Defaults to `jpg`.
    -   Example: `--ext png`
-   `--workers <number>`: The number of worker processes to use for conversion. Defaults to the number of CPU cores.
    -   Example: `--workers 4`

### Example

```bash
python cr3_converter.py /path/to/my/cr3_images /path/to/my/converted_images --ext jpg
```

This command will find all `.cr3` files in `/path/to/my/cr3_images`, convert them to JPEG, and save them in `/path/to/my/converted_images`.
