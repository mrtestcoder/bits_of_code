<#
.SYNOPSIS
    This script monitors for unusual file access patterns to identify potential data exfiltration.
.DESCRIPTION
    This script queries the security event log for file access events (Event ID 4663) and identifies users accessing an unusually high number of files within a specified timeframe. It also flags access outside of normal business hours.
.NOTES
    Author: Jules
    Date: 2025-07-19
#>

param (
    [int]$FileAccessThreshold = 100,
    [int]$TimeframeMinutes = 60,
    [int]$BusinessHourStart = 8, # 8 AM
    [int]$BusinessHourEnd = 18  # 6 PM
)

$EndTime = Get-Date
$StartTime = $EndTime.AddMinutes(-$TimeframeMinutes)

# Enable file access auditing on sensitive folders for this to work.
$FileAccessEvents = Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    ID = 4663
    StartTime = $StartTime
    EndTime = $EndTime
}

# Group by user and count file access events
$UserFileAccess = $FileAccessEvents | Group-Object -Property @{Expression={$_.Properties[1].Value}}

# Check for high volume access
$HighVolumeAccess = $UserFileAccess | Where-Object { $_.Count -ge $FileAccessThreshold }

if ($HighVolumeAccess) {
    Write-Output "High volume file access detected:"
    $HighVolumeAccess | ForEach-Object {
        Write-Output "  - User: $($_.Name), Files Accessed: $($_.Count)"
    }
}

# Check for access outside business hours
$OutsideHoursAccess = $FileAccessEvents | Where-Object {
    $EventTime = $_.TimeCreated
    $EventHour = $EventTime.Hour
    $EventDay = $EventTime.DayOfWeek
    ($EventHour -lt $BusinessHourStart -or $EventHour -ge $BusinessHourEnd) -or ($EventDay -eq [DayOfWeek]::Saturday -or $EventDay -eq [DayOfWeek]::Sunday)
}

if ($OutsideHoursAccess) {
    Write-Output "`nFile access outside of business hours detected:"
    $OutsideHoursAccess | ForEach-Object {
        $access_time = $_.TimeCreated
        $user = $_.Properties[1].Value
        $file = $_.Properties[6].Value
        Write-Output "  - User: $user accessed $file at $access_time"
    }
}

if (-not ($HighVolumeAccess -or $OutsideHoursAccess)) {
    Write-Output "No unusual file access patterns detected in the last $TimeframeMinutes minutes."
}
