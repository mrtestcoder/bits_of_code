import pandas as pd

def load_data(data_dir):
    """
    Load data from CSV files into pandas DataFrames.
    """
    vulnerabilities = pd.read_csv(f"{data_dir}/vulnerabilities.csv")
    findings = pd.read_csv(f"{data_dir}/findings.csv")
    amis = pd.read_csv(f"{data_dir}/amis.csv")
    accounts = pd.read_csv(f"{data_dir}/accounts.csv")
    return vulnerabilities, findings, amis, accounts

def correlate_data(vulnerabilities, findings, amis, accounts):
    """
    Correlate the data from the different DataFrames.
    """
    # Merge findings and vulnerabilities
    finding_vulns = pd.merge(findings, vulnerabilities, on="vulnerability_id")

    # Merge with AMIs
    finding_vulns.rename(columns={"asset_id": "ami_id"}, inplace=True)
    merged_data = pd.merge(finding_vulns, amis, on="ami_id", how="left")

    # Merge with accounts
    merged_data.rename(columns={"owner_id": "account_id"}, inplace=True)
    merged_data = pd.merge(merged_data, accounts, on="account_id", how="left")

    return merged_data

def analyze_and_prioritize(merged_data):
    """
    Analyze and prioritize the vulnerabilities.
    """
    # Create a scoring system for severity
    severity_scores = {"High": 3, "Medium": 2, "Low": 1}
    merged_data["severity_score"] = merged_data["severity"].map(severity_scores)

    # Prioritize by severity and number of affected systems
    ami_vuln_counts = merged_data.groupby("ami_id")["severity_score"].sum().sort_values(ascending=False).reset_index()
    ami_vuln_counts.rename(columns={"severity_score": "total_severity_score"}, inplace=True)

    prioritized_data = pd.merge(merged_data, ami_vuln_counts, on="ami_id").sort_values(by=["total_severity_score", "severity_score"], ascending=False)

    return prioritized_data

def generate_report(prioritized_data, output_file):
    """
    Generate a CSV report of the prioritized vulnerabilities.
    """
    prioritized_data.to_csv(output_file, index=False)
    print(f"Report generated successfully: {output_file}")

def main():
    """
    Main function to generate the Tenable report.
    """
    print("Starting Tenable report generation...")
    vulnerabilities, findings, amis, accounts = load_data("tenable_report")
    print("Data loaded successfully.")

    merged_data = correlate_data(vulnerabilities, findings, amis, accounts)

    prioritized_data = analyze_and_prioritize(merged_data)

    generate_report(prioritized_data, "tenable_report/vulnerability_report.csv")

if __name__ == "__main__":
    main()
