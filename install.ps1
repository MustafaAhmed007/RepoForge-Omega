param([string]$Target='.')
$ErrorActionPreference = 'Stop'
$Target = (Resolve-Path $Target).Path
$Source = Split-Path -Parent $MyInvocation.MyCommand.Path
$Venv = Join-Path $Target '.repoforge-venv'
python -m venv $Venv
& (Join-Path $Venv 'Scripts/python.exe') -m pip install --upgrade pip
& (Join-Path $Venv 'Scripts/python.exe') -m pip install -e $Source
Write-Host "RepoForge installed in $Venv"
Write-Host "Run: $Venv\Scripts\repoforge.exe inspect $Target"
