# Asset Tracker

This tool tracks externally facing assets using Shodan. It takes a list of IPs, queries Shodan for information about them, and generates an HTML report. It also tracks changes between scans, highlighting new and closed ports.

## Features

- Scans a list of IPs from a CSV file.
- Queries the Shodan API for detailed information.
- Tracks changes in open ports between scans.
- Generates a clean HTML report of the findings.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up your Shodan API key:**
    You can provide your Shodan API key in one of two ways:
    -   As an environment variable:
        ```bash
        export SHODAN_API_KEY="YOUR_API_KEY"
        ```
    -   As a command-line argument:
        ```bash
        python asset_tracker.py --api-key "YOUR_API_KEY"
        ```

3.  **Create your IP list:**
    Edit the `ips.csv` file and add the IP addresses you want to scan, one per line.

## Usage

To run the scanner, simply execute the script:

```bash
python asset_tracker.py
```

If you are not using an environment variable for the API key, you must provide it with the `--api-key` flag.

The script will perform the scan and generate a `report.html` file in the same directory. It will also create a `results/` directory to store the raw JSON data from Shodan for each IP, which is used for tracking changes over time.
