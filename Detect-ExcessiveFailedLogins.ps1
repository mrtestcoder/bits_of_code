<#
.SYNOPSIS
    This script detects excessive failed login attempts to identify potential brute-force attacks.
.DESCRIPTION
    This script queries the security event log for failed login events (Event ID 4625) and identifies user accounts with a high number of failed attempts within a specified timeframe.
.NOTES
    Author: Jules
    Date: 2025-07-19
#>

param (
    [int]$Threshold = 10,
    [int]$TimeframeHours = 24
)

$EndTime = Get-Date
$StartTime = $EndTime.AddHours(-$TimeframeHours)

$FailedLogins = Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    ID = 4625
    StartTime = $StartTime
    EndTime = $EndTime
}

$FailedLoginCounts = $FailedLogins | Group-Object -Property @{Expression={$_.Properties[5].Value}} | Where-Object { $_.Count -ge $Threshold }

if ($FailedLoginCounts) {
    Write-Output "Excessive failed login attempts detected for the following accounts:"
    $FailedLoginCounts | ForEach-Object {
        Write-Output "  - Account: $($_.Name), Failed Attempts: $($_.Count)"
    }
} else {
    Write-Output "No excessive failed login attempts detected within the last $TimeframeHours hours."
}
