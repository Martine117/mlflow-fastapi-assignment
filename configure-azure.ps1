# Dot-source in your own PowerShell: . .\configure-azure.ps1
$ErrorActionPreference = 'Stop'
$account = Read-Host 'Your Azure storage account name (not a secret)'
$container = Read-Host 'Your private blob container name (not a secret)'
if ($account -notmatch '^[a-z0-9]{3,24}$' -or $container -notmatch '^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$') {
    throw 'Invalid storage account or container name'
}
& .\.venv\Scripts\dvc.exe remote modify --local myazure url "azure://$container/mlflow-fastapi-assignment"
if ($LASTEXITCODE -ne 0) { throw 'Remote configuration failed' }
$env:AZURE_STORAGE_ACCOUNT = $account
$secureSas = Read-Host 'Fresh container SAS token (hidden, never paste in chat)' -AsSecureString
try {
    $env:AZURE_STORAGE_SAS_TOKEN = ([System.Net.NetworkCredential]::new('', $secureSas).Password).TrimStart('?')
} finally { Remove-Variable secureSas }
Write-Host 'Configured for this shell only. SAS was not saved to disk. Remote URL contains no credentials.'
