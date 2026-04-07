$ErrorActionPreference = "Stop"

$backendScript = Join-Path $PSScriptRoot "deploy-backend.ps1"
$frontendScript = Join-Path $PSScriptRoot "deploy-frontend.ps1"

Write-Host "[deploy] Running backend deploy"
& $backendScript @args

Write-Host "[deploy] Running frontend deploy"
& $frontendScript
