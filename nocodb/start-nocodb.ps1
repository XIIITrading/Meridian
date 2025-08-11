# Start NocoDB
Write-Host "=== Starting NocoDB ===" -ForegroundColor Cyan
Write-Host ""

# Check if .env.nocodb exists and is configured
if (!(Test-Path ".\.env.nocodb")) {
    Write-Host "ERROR: .env.nocodb not found!" -ForegroundColor Red
    Write-Host "Please configure .env.nocodb first" -ForegroundColor Yellow
    exit 1
}

# Check if DATABASE_URL is configured
$dbUrl = Select-String -Path ".\.env.nocodb" -Pattern "DATABASE_URL=.+" -Quiet
if (!$dbUrl) {
    Write-Host "WARNING: DATABASE_URL not configured in .env.nocodb" -ForegroundColor Yellow
    Write-Host "NocoDB will use local SQLite database" -ForegroundColor Yellow
}

# Load environment variables
Write-Host "Loading environment variables..." -ForegroundColor Yellow
Get-Content .\.env.nocodb | ForEach-Object {
    if ($_ -match '^([^#]\S+)=(.+)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

Write-Host "Starting NocoDB on http://localhost:8080" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start NocoDB using npx
npx nocodb
