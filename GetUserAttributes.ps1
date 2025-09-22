# Import the Active Directory module
Import-Module ActiveDirectory

# Prompt for the username
$userName = Read-Host -Prompt "Enter the username"

try {
    # Retrieve all attributes for the specified user
    $user = Get-ADUser -Identity $userName -Properties *
    if ($user) {
        $user | Format-List -Property *
    }
}
catch [Microsoft.ActiveDirectory.Management.ADIdentityNotFoundException] {
    Write-Warning "User '$userName' not found in Active Directory."
}
catch {
    Write-Error "An unexpected error occurred: $($_.Exception.Message)"
}
