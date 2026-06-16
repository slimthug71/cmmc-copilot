$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$Port = if ($args.Count -gt 0) { $args[0] } else { "8001" }

if (-not (Test-Path $Python)) {
    Write-Error "Backend virtual environment was not found at $Python"
    exit 1
}

Set-Location $Backend
& $Python -m uvicorn app.main:app --reload --port $Port
