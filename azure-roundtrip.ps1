# Run only after dot-sourcing configure-azure.ps1. No secrets printed.
$ErrorActionPreference = 'Stop'
function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed; see preceding output" }
}
if (-not $env:AZURE_STORAGE_ACCOUNT -or -not $env:AZURE_STORAGE_SAS_TOKEN) {
    throw 'Configure Azure in this PowerShell session first'
}
$originalBranch = git branch --show-current
if (-not $originalBranch) { throw 'Start on a named branch' }
if (git status --porcelain) { throw 'Commit reviewed non-secret configuration changes first' }
$dvc = '.\.venv\Scripts\dvc.exe'
try {
    # Push both tag-referenced objects, not only the current dataset.
    Invoke-Checked $dvc @('push', '--all-tags', '-r', 'myazure')
    foreach ($version in @(1, 2)) {
        Invoke-Checked 'git' @('switch', '--detach', "dvc-demo-v$version")
        # A fresh ignored cache forces a real remote fetch without deleting the original cache.
        $freshCache = Join-Path $env:TEMP ("dvc-azure-proof-" + [guid]::NewGuid().ToString('N'))
        Invoke-Checked $dvc @('cache', 'dir', '--local', $freshCache)
        Invoke-Checked $dvc @('pull', '-r', 'myazure')
        Invoke-Checked '.\.venv\Scripts\python.exe' @('verify_dvc.py', '--version', "$version")
    }
} finally {
    & $dvc config --local --unset cache.dir
    Invoke-Checked 'git' @('switch', $originalBranch)
    Invoke-Checked $dvc @('checkout')
}
Write-Host 'Both Azure uploads and fresh-cache restores passed. Returned to original branch.'
