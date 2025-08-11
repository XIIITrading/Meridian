# NocoDB Setup Script
Write-Host "=== NocoDB Local Setup ===" -ForegroundColor Cyan
Write-Host "All files will be created in: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# 1. Create necessary subdirectories
Write-Host "Creating directory structure..." -ForegroundColor Yellow
$dirs = @(".\data", ".\config", ".\logs")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "  ✓ Created $dir" -ForegroundColor Green
    } else {
        Write-Host "  ✓ $dir exists" -ForegroundColor Green
    }
}

# 2. Check for required files
Write-Host "`nChecking configuration files..." -ForegroundColor Yellow
$requiredFiles = @(".env.nocodb", "package.json")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $file needs to be created" -ForegroundColor Yellow
    }
}

Write-Host "`n✓ NocoDB directory is ready!" -ForegroundColor Green
Write-Host "Next: Configure .env.nocodb with your Supabase credentials" -ForegroundColor Cyan
