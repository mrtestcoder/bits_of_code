# AWS IAM User Audit Script

This Python script exports information about IAM user accounts in an AWS environment.
It is designed to help audit when user assets (like the user account itself or access keys)
were created and their current status. The output is a CSV file named `iam_user_audit_report.csv`.

## Prerequisites

1.  **Python 3**: Ensure Python 3.6 or newer is installed.
2.  **Boto3**: The AWS SDK for Python. If you don't have it installed, you can install it using pip:
    ```bash
    pip install boto3
    ```

## AWS Credentials Configuration

The script uses `boto3` to interact with your AWS account. `boto3` will look for credentials in the following order:

1.  **Environment Variables**:
    *   `AWS_ACCESS_KEY_ID`
    *   `AWS_SECRET_ACCESS_KEY`
    *   `AWS_SESSION_TOKEN` (optional, for temporary credentials)
    *   `AWS_DEFAULT_REGION` (e.g., `us-east-1`)
2.  **Shared Credential File**: Located at `~/.aws/credentials` (on Linux or macOS) or `C:\Users\USERNAME\.aws\credentials` (on Windows).
3.  **AWS IAM Roles for Amazon EC2**: If running on an EC2 instance with an IAM role assigned.

For most local development scenarios, configuring environment variables or the shared credential file is common.
Ensure the IAM identity (user or role) whose credentials are used has sufficient permissions to perform the following actions:
*   `iam:ListUsers`
*   `iam:GetAccessKeyLastUsed`
*   `iam:ListAccessKeys`
*   `iam:ListMFADevices`
*   `iam:GetUser` (implicitly used by some calls, good to have)

A managed policy like `IAMReadOnlyAccess` would generally be sufficient.

## How to Run the Script

1.  **Save the script**: Download or save the `aws_user_audit.py` script to your local machine.
2.  **Configure AWS Credentials**: Ensure your AWS credentials and default region are configured as described above.
3.  **Navigate to the script directory**: Open your terminal or command prompt and change to the directory where you saved the script.
    ```bash
    cd path/to/your/script_directory
    ```
4.  **Execute the script**:
    ```bash
    python aws_user_audit.py
    ```
    The script will print logging information to the console, indicating its progress.

## Output CSV File (`iam_user_audit_report.csv`)

Upon successful execution, the script will generate a CSV file named `iam_user_audit_report.csv` in the same directory.
This file contains the following columns:

*   `UserName`: The friendly name of the IAM user.
*   `UserId`: The unique ID of the IAM user.
*   `Arn`: The Amazon Resource Name (ARN) of the IAM user.
*   `CreateDate`: The date and time when the IAM user was created (ISO 8601 format).
*   `PasswordLastUsed`: The date and time the user's password was last used to sign in. 'N/A' if never used or no console password.
*   `MFAEnabled`: 'Yes' if MFA is enabled for the user, 'No' otherwise. 'Error' if status couldn't be determined.
*   `MFADevicesCount`: The number of MFA devices registered for the user. 'Error' if status couldn't be determined.
*   `AccessKeyId`: The ID of an access key associated with the user. Each access key will be on a new row. 'N/A' if the user has no access keys.
*   `AccessKeyStatus`: The status of the access key (e.g., `Active`, `Inactive`). 'N/A' if no access key.
*   `AccessKeyCreateDate`: The creation date of the access key (ISO 8601 format). 'N/A' if no access key.
*   `AccessKeyLastUsedDate`: The date and time the access key was last used. 'N/A' if never used or not determinable. 'Error retrieving last use' if an error occurred.
*   `AccessKeyLastUsedService`: The AWS service last accessed with this key. 'N/A' if never used or not determinable.
*   `AccessKeyLastUsedRegion`: The AWS region last accessed with this key. 'N/A' if never used or not determinable.

**Note**: If a user has multiple access keys, that user will appear on multiple rows in the CSV, with each row detailing one of their access keys. Users with no access keys will appear on a single row with 'N/A' in the access key-specific columns.
