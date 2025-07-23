# Tenable Vulnerability Report Generator

This project aims to create a Python-based report generator that processes Tenable One exports to identify high-impact vulnerabilities and provide actionable insights.

## Plan

1.  **Understand the Tenable One Export Format:** Research the structure of the Tenable One export files (Vulnerabilities, Findings, AMIs, Accounts) to understand their relationships.
2.  **Load and Process the Data:** Develop Python scripts to load the data from the spreadsheets into pandas DataFrames.
3.  **Correlate the Data:** Identify common fields (e.g., AMI ID) to link the different datasets.
4.  **Analyze and Prioritize:** Create a scoring system to rank vulnerabilities based on severity, number of affected systems, and asset type.
5.  **Generate a Report:** Produce a summary report (e.g., CSV, HTML, or PDF) with a prioritized list of actions.
