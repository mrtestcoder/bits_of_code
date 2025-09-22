#Requires -Module ActiveDirectory

[CmdletBinding()]
param (
    [Parameter(HelpMessage = "Optional. Specify the target Active Directory domain. If not provided, the script will use the local domain of the machine.")]
    [string]$Domain
)

<#
.SYNOPSIS
    Retrieves a list of Active Directory users with their last logon date.

.DESCRIPTION
    This script queries Active Directory for all users and outputs their username, full name, last logon date, and the number of days since they last logged on.
    The output is displayed on the console and also exported to a CSV file named "ADUserLastLogon.csv" in the script's directory.

.NOTES
    Author: Jules
    Requires the Active Directory module for PowerShell. This is typically installed as part of the Remote Server Administration Tools (RSAT).
#>

try {
    # Check if the Active Directory module is available
    if (-not (Get-Module -ListAvailable -Name ActiveDirectory)) {
        Write-Warning "The Active Directory module is not available. Please install the Remote Server Administration Tools (RSAT)."
        # The script will likely fail on the next command, but this provides a clearer error.
        return # Exit if the required module is not there.
    }

    # If no domain is specified, default to the current domain
    if (-not $Domain) {
        try {
            $Domain = (Get-ADDomain).DNSRoot
            Write-Host "No domain specified. Defaulting to local domain: $Domain" -ForegroundColor Green
        }
        catch {
            Write-Error "Could not automatically determine the local domain. Please specify the domain using the -Domain parameter."
            # Exit the script if we can't determine the domain
            return
        }
    }

    # Get the current date for calculation
    $currentDate = Get-Date

    # Get all AD users and their last logon information
    # The LastLogon property is not replicated, so LastLogonDate is a calculated property that is more reliable.
    # It is replicated from the LastLogonTimeStamp attribute from all domain controllers.
    # The default search base is the entire domain.
    $users = Get-ADUser -Filter * -Properties Name, LastLogonDate, whenCreated -Server $Domain

    # Process the user list
    $userList = foreach ($user in $users) {
        $lastLogon = $user.LastLogonDate
        $daysSinceLastLogon = "N/A"

        if ($lastLogon) {
            $timespan = $currentDate - $lastLogon
            $daysSinceLastLogon = $timespan.Days
        } else {
            # If LastLogonDate is null, it could mean the user has never logged on.
            $lastLogon = "Never"
        }

        [PSCustomObject]@{
            Username             = $user.SamAccountName
            Name                 = $user.Name
            'Creation Date'      = $user.whenCreated
            'Last Logon Date'    = $lastLogon
            'Days Since Last Logon' = $daysSinceLastLogon
        }
    }

    # Output to console
    $userList | Format-Table

    # Export to CSV
    try {
        $documentsPath = [Environment]::GetFolderPath('MyDocuments')
        $csvPath = Join-Path -Path $documentsPath -ChildPath "ADUserLastLogon.csv"
        $userList | Export-Csv -Path $csvPath -NoTypeInformation
        Write-Host "Script finished. Results exported to '$csvPath'" -ForegroundColor Green
    }
    catch {
        Write-Warning "Could not export to CSV. Error: $_"
    }

}
catch {
    Write-Error "An error occurred: $_"
}
