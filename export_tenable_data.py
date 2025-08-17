from tenable.cloudsecurity import CloudSecurity

# This script exports all assets and vulnerabilities from Tenable.io Cloud Security.
#
# Before running this script, make sure you have the following environment variables set:
#   - TCS_URL: The URL of your Tenable.io Cloud Security instance.
#   - TCS_API_KEY: Your Tenable.io API key.
#
# You can run this script from the command line using the following command:
#   python export_tenable_data.py

def export_assets(cs):
    """
    Exports all compute and container assets from Tenable.io Cloud Security.
    Args:
        cs (CloudSecurity): An instance of the CloudSecurity class.
    Returns:
        A tuple containing two lists: one for compute assets and one for container assets.
    """
    print("Exporting assets...")
    compute_assets = [asset for asset in cs.assets.compute()]
    container_assets = [asset for asset in cs.assets.container()]
    print(f"Found {len(compute_assets)} compute assets.")
    print(f"Found {len(container_assets)} container assets.")
    return compute_assets, container_assets


def export_vulnerabilities(cs):
    """
    Exports all container and virtual machine vulnerabilities from Tenable.io Cloud Security.
    Args:
        cs (CloudSecurity): An instance of the CloudSecurity class.
    Returns:
        A tuple containing two lists: one for container image vulnerabilities and one for virtual machine vulnerabilities.
    """
    print("Exporting vulnerabilities...")
    container_vulns = [vuln for vuln in cs.vulns.containerimages()]
    vm_vulns = [vuln for vuln in cs.vulns.virtualmachines()]
    print(f"Found {len(container_vulns)} container image vulnerabilities.")
    print(f"Found {len(vm_vulns)} virtual machine vulnerabilities.")
    return container_vulns, vm_vulns


if __name__ == "__main__":
    # Instantiate the CloudSecurity class.
    # The SDK will automatically pull the URL and API key from the environment variables.
    cs = CloudSecurity()

    # Export all assets and vulnerabilities.
    all_assets = export_assets(cs)
    all_vulnerabilities = export_vulnerabilities(cs)

    # Print the results.
    print("\n--- Assets ---")
    print("Compute Assets:", all_assets[0])
    print("Container Assets:", all_assets[1])
    print("\n--- Vulnerabilities ---")
    print("Container Image Vulnerabilities:", all_vulnerabilities[0])
    print("Virtual Machine Vulnerabilities:", all_vulnerabilities[1])
