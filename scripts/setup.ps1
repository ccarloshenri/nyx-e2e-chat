$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot

Write-Host "[setup] Preparing Nyx project environment"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "[setup] npm is required but was not found"
}

$pythonCommand = $null
$pythonArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = "py"
    $pythonArgs = @("-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = "python"
} else {
    throw "[setup] Python 3.12+ is required but was not found"
}

Write-Host "[setup] Installing frontend dependencies"
Set-Location (Join-Path $RootDir "frontend")
npm install

if (-not (Test-Path ".env.local")) {
    Copy-Item ".env.example" ".env.local"
    Write-Host "[setup] Created frontend/.env.local from .env.example"
}

Write-Host "[setup] Installing backend dependencies"
Set-Location (Join-Path $RootDir "backend")
& $pythonCommand @pythonArgs -m venv .venv

if ($LASTEXITCODE -ne 0) {
    Write-Warning "[setup] Virtual environment creation failed, falling back to the system interpreter"
}

$venvPython = Join-Path $PWD ".venv\Scripts\python.exe"
$pythonInstallerCommand = $pythonCommand
$pythonInstallerArgs = @($pythonArgs)

if (Test-Path $venvPython) {
    $pythonInstallerCommand = $venvPython
    $pythonInstallerArgs = @()
} else {
    Write-Warning "[setup] Backend virtual environment Python was not created successfully. Using the system interpreter instead."
}

& $pythonInstallerCommand @pythonInstallerArgs -m pip install -r requirements.txt
& $pythonInstallerCommand @pythonInstallerArgs -m pip install -e ".[dev]"

Write-Host "[setup] Local setup complete"
Write-Host "[setup] Backend and frontend dependencies are ready"
