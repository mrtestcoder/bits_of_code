<#
.SYNOPSIS
    This script identifies stale user accounts that have not been used for a specified period.
.DESCRIPTION
    This script queries Active Directory for user accounts that have not logged in for a specified number of days.
.NOTES
    Author: Jules
    Date: 2025-07-19
#>

param (
    [int]$InactiveDays = 90
)

$StaleDate = (Get-Date).AddDays(-$InactiveDays)

# Requires Active Directory module
Import-Module ActiveDirectory

Get-ADUser -Filter {LastLogonDate -lt $StaleDate -and Enabled -eq $true} -Properties LastLogonDate |
    Select-Object Name, SamAccountName, DistinguishedName, LastLogonDate |
    Sort-Object LastLogonDate |
    ForEach-Object {
        Write-Output "Stale Account Found:"
        Write-Output "  - Name: $($_.Name)"
        Write-Output "  - Logon Name: $($_.SamAccountName)"
        Write-Output "  - Last Logon: $($_.LastLogonDate)"
        Write-Output "  - DN: $($_.DistinguishedName)"
        Write-Output ""
    }
