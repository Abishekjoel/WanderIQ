<#
    AI Travel Planner - backend launcher
    Starts ONLY this project's FastAPI backend, from this project's own folder,
    with this project's own virtual environment, on this project's own port.
#>

$ErrorActionPreference = 'Stop'

# 1. Always run from THIS project's root, whatever the caller's location was.
Set-Location -Path $PSScriptRoot

$Project = 'AI Travel Planner'
$Port    = 8001
$AppPath = 'backend.main:app'

# 2. Pick this project's own interpreter (venv if present, else system python).
$venvPy = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'
if (Test-Path $venvPy) { $python = $venvPy } else { $python = 'python' }

# 3. Refuse to start if the port is already taken - show WHO has it, do not kill.
$conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    $owner = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    if ($owner -and $owner.Path) { $ownerName = $owner.Path } elseif ($owner) { $ownerName = $owner.ProcessName } else { $ownerName = '(process not visible - may be elevated; use an Administrator PowerShell)' }
    Write-Host "Port $Port is already in use - $Project will NOT start." -ForegroundColor Red
    Write-Host ("  PID {0}  {1}" -f $conn.OwningProcess, $ownerName) -ForegroundColor Yellow
    Write-Host "  Inspect : netstat -ano | findstr :$Port"
    Write-Host "  Then    : Get-Process -Id $($conn.OwningProcess)"
    Write-Host "  Stop it : Stop-Process -Id $($conn.OwningProcess)   # only if it is a stale server you own"
    exit 1
}

Write-Host "Starting $Project backend -> http://127.0.0.1:$Port  (docs: /docs, identity: /health)" -ForegroundColor Green

# 4. --reload-dir backend keeps the file-watcher INSIDE this project only.
& $python -m uvicorn $AppPath --host 127.0.0.1 --port $Port --reload --reload-dir (Join-Path $PSScriptRoot 'backend')
