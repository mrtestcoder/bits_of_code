<#
.SYNOPSIS
    This script audits the current password policies to ensure they meet the bank's security requirements.
.DESCRIPTION
    This script retrieves the domain's default password policy and compares it against a set of recommended baseline values.
.NOTES
    Author: Jules
    Date: 2025-07-19
#>

# Requires Active Directory module
Import-Module ActiveDirectory

$Policy = Get-ADDefaultDomainPasswordPolicy

Write-Host "Auditing Domain Password Policy..."
Write-Host "----------------------------------"

# Minimum Password Length
$MinLength = 12
if ($Policy.MinPasswordLength -lt $MinLength) {
    Write-Host "FAIL: Minimum password length is $($Policy.MinPasswordLength), should be at least $MinLength characters." -ForegroundColor Red
} else {
    Write-Host "PASS: Minimum password length is $($Policy.MinPasswordLength)." -ForegroundColor Green
}

# Password History
$MinHistory = 24
if ($Policy.PasswordHistoryCount -lt $MinHistory) {
    Write-Host "FAIL: Password history count is $($Policy.PasswordHistoryCount), should be at least $MinHistory." -ForegroundColor Red
} else {
    Write-Host "PASS: Password history count is $($Policy.PasswordHistoryCount)." -ForegroundColor Green
}

# Maximum Password Age
$MaxAgeDays = 60
if ($Policy.MaxPasswordAge.Days -gt $MaxAgeDays) {
    Write-Host "FAIL: Maximum password age is $($Policy.MaxPasswordAge.Days) days, should be no more than $MaxAgeDays days." -ForegroundColor Red
} else {
    Write-Host "PASS: Maximum password age is $($Policy.MaxPasswordAge.Days) days." -ForegroundColor Green
}

# Minimum Password Age
$MinAgeDays = 1
if ($Policy.MinPasswordAge.Days -lt $MinAgeDays) {
    Write-Host "FAIL: Minimum password age is $($Policy.MinPasswordAge.Days) days, should be at least $MinAgeDays day." -ForegroundColor Red
} else {
    Write-Host "PASS: Minimum password age is $($Policy.MinPasswordAge.Days) days." -ForegroundColor Green
}

# Password Complexity
if (-not $Policy.ComplexityEnabled) {
    Write-Host "FAIL: Password complexity is not enabled." -ForegroundColor Red
} else {
    Write-Host "PASS: Password complexity is enabled." -ForegroundColor Green
}

# Reversible Encryption
if ($Policy.ReversibleEncryptionEnabled) {
    Write-Host "FAIL: Reversible encryption is enabled. This is a major security risk." -ForegroundColor Red
} else {
    Write-Host "PASS: Reversible encryption is not enabled." -ForegroundColor Green
}

Write-Host "----------------------------------"
Write-Host "Audit Complete."
