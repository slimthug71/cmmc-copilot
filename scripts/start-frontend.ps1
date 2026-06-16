$Root = Split-Path -Parent $PSScriptRoot
$Frontend = Join-Path $Root "frontend"
$Node = "C:\Program Files\nodejs\node.exe"
$Next = Join-Path $Frontend "node_modules\next\dist\bin\next"
$Port = if ($args.Count -gt 0) { $args[0] } else { "3000" }

if (-not (Test-Path $Node)) {
    Write-Error "Node.js was not found at $Node"
    exit 1
}

if (-not (Test-Path $Next)) {
    Write-Error "Next.js was not found at $Next. Run npm install in the frontend folder."
    exit 1
}

$env:NODE_OPTIONS = "--openssl-legacy-provider"
Set-Location $Frontend
& $Node $Next dev -p $Port
