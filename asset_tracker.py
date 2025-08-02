import argparse
import csv
import shodan
import json
import os
from datetime import datetime

RESULTS_DIR = "results"

def read_ips_from_csv(filepath):
    """Reads a list of IPs from a CSV file."""
    ips = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                ips.append(row[0])
    return ips

def get_shodan_info(api_key, ip):
    """Queries the Shodan API for information about a given IP."""
    api = shodan.Shodan(api_key)
    try:
        host_info = api.host(ip)
        return host_info
    except shodan.APIError as e:
        print(f"Error querying Shodan for {ip}: {e}")
        return None

def save_results(ip, data):
    """Saves the scan results to a JSON file."""
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    filepath = os.path.join(RESULTS_DIR, f"{ip}.json")
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def load_previous_results(ip):
    """Loads previous scan results from a JSON file."""
    filepath = os.path.join(RESULTS_DIR, f"{ip}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def compare_results(previous, current):
    """Compares previous and current scan results and returns the deltas."""
    deltas = {}

    prev_ports = set(item['port'] for item in previous.get('data', []))
    curr_ports = set(item['port'] for item in current.get('data', []))

    new_ports = curr_ports - prev_ports
    closed_ports = prev_ports - curr_ports

    if new_ports:
        deltas['new_ports'] = sorted(list(new_ports))
    if closed_ports:
        deltas['closed_ports'] = sorted(list(closed_ports))

    return deltas

def generate_html_report(all_results, all_deltas):
    """Generates an HTML report from the scan results and deltas."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
<html>
<head>
    <title>Asset Tracker Report</title>
    <style>
        body {{ font-family: sans-serif; }}
        h1, h2, h3 {{ color: #333; }}
        .container {{ width: 80%; margin: auto; }}
        .ip-block {{ border: 1px solid #ccc; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
        .ports li {{ list-style-type: none; background: #f0f0f0; margin: 5px 0; padding: 5px; border-radius: 3px; }}
        .deltas {{ color: #d9534f; }}
        .new-ports {{ color: #5cb85c; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Asset Tracker Report - {now}</h1>
    """

    for ip, results in all_results.items():
        html += f"""
        <div class="ip-block">
            <h2>{ip}</h2>
        """

        # Display Deltas
        if ip in all_deltas and all_deltas[ip]:
            deltas = all_deltas[ip]
            html += "<h3>Changes Detected</h3>"
            if 'new_ports' in deltas:
                html += f"<p class='new-ports'>New Open Ports: {', '.join(map(str, deltas['new_ports']))}</p>"
            if 'closed_ports' in deltas:
                html += f"<p class='deltas'>Closed Ports: {', '.join(map(str, deltas['closed_ports']))}</p>"

        # Display Hostnames
        hostnames = ', '.join(results.get('hostnames', []))
        if hostnames:
            html += f"<h3>Hostnames</h3><p>{hostnames}</p>"

        # Display Open Ports
        if results.get('data'):
            html += "<h3>Open Ports</h3><ul class='ports'>"
            for item in results['data']:
                html += f"<li><b>{item['port']}/{item.get('transport', 'tcp')}</b> - {item.get('_shodan', {}).get('module', 'N/A')}</li>"
            html += "</ul>"

        html += "</div>"

    html += """
    </div>
</body>
</html>
    """
    with open("report.html", "w") as f:
        f.write(html)
    print("\nHTML report generated: report.html")

def main():
    parser = argparse.ArgumentParser(description="Track externally facing assets using Shodan.")
    parser.add_argument("--api-key", help="Your Shodan API key.")
    parser.add_argument("--ip-file", default="ips.csv", help="Path to the CSV file containing a list of IPs.")

    args = parser.parse_args()

    if not args.api_key:
        # For automated testing, we can allow the key to be passed as an env var
        args.api_key = os.environ.get('SHODAN_API_KEY')
        if not args.api_key:
            parser.error("Shodan API key is required. Use --api-key or set SHODAN_API_KEY environment variable.")

    ips = read_ips_from_csv(args.ip_file)
    print(f"Loaded {len(ips)} IPs from {args.ip_file}")

    all_results = {}
    all_deltas = {}

    for ip in ips:
        print(f"\nProcessing {ip}...")

        previous_results = load_previous_results(ip)
        current_results = get_shodan_info(args.api_key, ip)

        if current_results:
            all_results[ip] = current_results
            if previous_results:
                deltas = compare_results(previous_results, current_results)
                if deltas:
                    all_deltas[ip] = deltas
                    print(f"  Changes detected for {ip}.")
                else:
                    print(f"  No changes detected for {ip}.")
            else:
                print(f"  First scan for {ip}. Saving results.")

            save_results(ip, current_results)
        else:
            print(f"  Could not retrieve information for {ip}.")

    if all_results:
        generate_html_report(all_results, all_deltas)

    print("\nScan complete.")

if __name__ == "__main__":
    main()
