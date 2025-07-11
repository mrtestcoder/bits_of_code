import boto3
import csv
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_iam_user_data(iam_client):
    """
    Fetches IAM user data from AWS.
    :param iam_client: Initialized boto3 IAM client.
    :return: A list of dictionaries, where each dictionary contains info for one user.
    """
    users_data = []
    logging.info("Starting to fetch IAM user list...")

    try:
        paginator = iam_client.get_paginator('list_users')
        for page_num, page in enumerate(paginator.paginate(), 1):
            logging.info(f"Processing page {page_num} of users...")
            for user in page.get('Users', []):
                user_name = user['UserName']
                logging.info(f"Fetching details for user: {user_name}")
                user_info = {
                    'UserName': user_name,
                    'UserId': user['UserId'],
                    'Arn': user['Arn'],
                    'CreateDate': user['CreateDate'].isoformat() if 'CreateDate' in user else 'N/A',
                    'PasswordLastUsed': user.get('PasswordLastUsed', 'N/A')
                }
                if user_info['PasswordLastUsed'] != 'N/A' and not isinstance(user_info['PasswordLastUsed'], str):
                    user_info['PasswordLastUsed'] = user_info['PasswordLastUsed'].isoformat()

                # Get MFA devices
                try:
                    mfa_devices_response = iam_client.list_mfa_devices(UserName=user_name)
                    user_info['MFAEnabled'] = 'Yes' if mfa_devices_response.get('MFADevices') else 'No'
                    # Storing only the count for simplicity in the main user record for CSV
                    user_info['MFADevicesCount'] = len(mfa_devices_response.get('MFADevices', []))
                except Exception as e:
                    logging.error(f"Could not retrieve MFA devices for user {user_name}: {e}")
                    user_info['MFAEnabled'] = 'Error'
                    user_info['MFADevicesCount'] = 'Error'


                # Get Access Keys
                user_info['AccessKeys'] = []
                try:
                    keys_paginator = iam_client.get_paginator('list_access_keys')
                    for keys_page_num, keys_page in enumerate(keys_paginator.paginate(UserName=user_name), 1):
                        logging.debug(f"Processing page {keys_page_num} of access keys for user {user_name}...")
                        for key in keys_page.get('AccessKeyMetadata', []):
                            key_id = key['AccessKeyId']
                            key_status = key['Status']
                            key_create_date = key['CreateDate'].isoformat()

                            key_last_used_date = 'N/A'
                            key_last_used_service = 'N/A'
                            key_last_used_region = 'N/A'

                            try:
                                last_used_response = iam_client.get_access_key_last_used(AccessKeyId=key_id)
                                if 'AccessKeyLastUsed' in last_used_response and last_used_response['AccessKeyLastUsed']:
                                    if 'LastUsedDate' in last_used_response['AccessKeyLastUsed']:
                                        key_last_used_date = last_used_response['AccessKeyLastUsed']['LastUsedDate'].isoformat()
                                    key_last_used_service = last_used_response['AccessKeyLastUsed'].get('ServiceName', 'N/A')
                                    key_last_used_region = last_used_response['AccessKeyLastUsed'].get('Region', 'N/A')
                            except Exception as e:
                                logging.warning(f"Could not get last used info for access key {key_id} for user {user_name}: {e}")
                                key_last_used_date = 'Error retrieving last use'


                            user_info['AccessKeys'].append({
                                'AccessKeyId': key_id,
                                'Status': key_status,
                                'CreateDate': key_create_date,
                                'LastUsedDate': key_last_used_date,
                                'LastUsedService': key_last_used_service,
                                'LastUsedRegion': key_last_used_region
                            })
                except Exception as e:
                    logging.error(f"Could not retrieve access keys for user {user_name}: {e}")

                users_data.append(user_info)
        logging.info("Successfully fetched all IAM user data.")
        return users_data

    except boto3.exceptions.NoCredentialsError:
        logging.error("AWS credentials not found. Please configure your credentials (e.g., AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN).")
        return []
    except Exception as e:
        logging.error(f"Error fetching IAM user list: {e}")
        return []

def write_to_csv(users_data_list, filename="iam_user_audit_report.csv"):
    """
    Writes the collected user data to a CSV file.
    Each access key will result in a separate row in the CSV for easier analysis.
    Users without access keys will still be listed.
    :param users_data_list: List of user data dictionaries from get_iam_user_data.
    :param filename: The name of the CSV file to write.
    """
    if not users_data_list:
        logging.warning("No data to write to CSV.")
        return

    # Define the fieldnames for the CSV.
    fieldnames = [
        'UserName', 'UserId', 'Arn', 'CreateDate', 'PasswordLastUsed',
        'MFAEnabled', 'MFADevicesCount',
        'AccessKeyId', 'AccessKeyStatus', 'AccessKeyCreateDate',
        'AccessKeyLastUsedDate', 'AccessKeyLastUsedService', 'AccessKeyLastUsedRegion'
    ]

    processed_rows = []
    for user_record in users_data_list:
        base_user_info = {
            'UserName': user_record['UserName'],
            'UserId': user_record['UserId'],
            'Arn': user_record['Arn'],
            'CreateDate': user_record['CreateDate'],
            'PasswordLastUsed': user_record['PasswordLastUsed'],
            'MFAEnabled': user_record['MFAEnabled'],
            'MFADevicesCount': user_record['MFADevicesCount']
        }

        if user_record.get('AccessKeys'):
            for key in user_record['AccessKeys']:
                row = base_user_info.copy()
                row.update({
                    'AccessKeyId': key['AccessKeyId'],
                    'AccessKeyStatus': key['Status'],
                    'AccessKeyCreateDate': key['CreateDate'],
                    'AccessKeyLastUsedDate': key['LastUsedDate'],
                    'AccessKeyLastUsedService': key['LastUsedService'],
                    'AccessKeyLastUsedRegion': key['LastUsedRegion']
                })
                processed_rows.append(row)
        else:
            # User has no access keys, still add their info with N/A for key fields
            row = base_user_info.copy()
            row.update({
                'AccessKeyId': 'N/A',
                'AccessKeyStatus': 'N/A',
                'AccessKeyCreateDate': 'N/A',
                'AccessKeyLastUsedDate': 'N/A',
                'AccessKeyLastUsedService': 'N/A',
                'AccessKeyLastUsedRegion': 'N/A'
            })
            processed_rows.append(row)

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(processed_rows)
        logging.info(f"Successfully wrote IAM user audit data to {filename}")
    except IOError as e:
        logging.error(f"Error writing to CSV file {filename}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during CSV writing: {e}")

def main():
    """
    Main function to orchestrate IAM user audit.
    """
    logging.info("Starting IAM user audit script...")

    try:
        # It's good practice to initialize the client once and pass it around.
        iam_client = boto3.client('iam')
    except Exception as e:
        logging.error(f"Failed to initialize Boto3 IAM client: {e}. Ensure AWS credentials and region are configured.")
        return

    user_audit_data = get_iam_user_data(iam_client)

    if user_audit_data:
        write_to_csv(user_audit_data)
    else:
        logging.warning("No user data retrieved. Audit report not generated.")

    logging.info("IAM user audit script finished.")

if __name__ == "__main__":
    main()
