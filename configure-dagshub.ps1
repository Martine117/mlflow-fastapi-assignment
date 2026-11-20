# Dot-source: . .\configure-dagshub.ps1
$env:MLFLOW_TRACKING_URI = 'https://dagshub.com/Martine117/mlflow-digits.mlflow'
$env:MLFLOW_TRACKING_USERNAME = 'Martine117'
$dagshubSecret = Read-Host 'DagsHub token (hidden)' -AsSecureString
try {
    $env:MLFLOW_TRACKING_PASSWORD = [System.Net.NetworkCredential]::new('', $dagshubSecret).Password
} finally {
    Remove-Variable dagshubSecret
}
Write-Host 'DagsHub configured for this shell. Token was not saved to a file.'
