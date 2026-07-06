# =====================================================================
#  Pacific Research Group LLC — SAM.gov Automation Setup (run once)
# =====================================================================
#  Sets up hands-off scheduled scans that save date-stamped reports to:
#      Desktop\PRG_SAMgov_Reports\Weekly    (Mondays 9:00 AM, last 10 days)
#      Desktop\PRG_SAMgov_Reports\Monthly   (1st of month 9:00 AM, last 90 days)
#
#  Run it once by pasting this into PowerShell:
#    iex (irm "https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/claude/samgov-opportunity-matcher-0a3c2f/automation/setup_prg_automation.ps1")
# =====================================================================

$ErrorActionPreference = 'Stop'
$branchRaw = 'https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/claude/samgov-opportunity-matcher-0a3c2f/samgov_opportunity_matcher.py'

Write-Host ''
Write-Host '=== PRG SAM.gov automation setup ===' -ForegroundColor Cyan

# 1. Folders
$root    = Join-Path $env:USERPROFILE 'Desktop\PRG_SAMgov_Reports'
$weekly  = Join-Path $root 'Weekly'
$monthly = Join-Path $root 'Monthly'
$null = New-Item -ItemType Directory -Force -Path $root, $weekly, $monthly
Write-Host "  Reports folder: $root" -ForegroundColor Green

# 2. Download the latest matcher script
$script = Join-Path $root 'samgov_opportunity_matcher.py'
Write-Host '  Downloading latest matcher script...' -ForegroundColor Cyan
Invoke-WebRequest $branchRaw -OutFile $script

# 3. Make sure Python packages are present
Write-Host '  Installing Python packages (requests, openpyxl)...' -ForegroundColor Cyan
try { py -m pip install --quiet --upgrade requests openpyxl }
catch { Write-Host '  (pip step skipped — check Python is installed)' -ForegroundColor Yellow }

# 4. Runner .bat files (keeps the scheduled-task command simple)
$weeklyBat  = Join-Path $root 'run_weekly.bat'
$monthlyBat = Join-Path $root 'run_monthly.bat'
Set-Content $weeklyBat  "@echo off`r`npy `"%~dp0samgov_opportunity_matcher.py`" --days 10 --outdir `"%~dp0Weekly`"`r`n"  -Encoding ASCII
Set-Content $monthlyBat "@echo off`r`npy `"%~dp0samgov_opportunity_matcher.py`" --days 90 --outdir `"%~dp0Monthly`"`r`n" -Encoding ASCII

# 5. Register scheduled tasks (schtasks handles weekly + monthly cleanly)
Write-Host '  Registering scheduled tasks...' -ForegroundColor Cyan
schtasks /Create /TN 'PRG SAMgov Weekly Scan'    /TR "`"$weeklyBat`""  /SC WEEKLY  /D MON /ST 09:00 /F | Out-Null
schtasks /Create /TN 'PRG SAMgov Monthly Report' /TR "`"$monthlyBat`"" /SC MONTHLY /D 1   /ST 09:00 /F | Out-Null

# 6. Run one scan now so you have fresh files immediately
Write-Host '  Running a first scan now (this takes a minute)...' -ForegroundColor Cyan
py $script --days 30 --outdir $weekly

Write-Host ''
Write-Host '=== Setup complete ===' -ForegroundColor Green
Write-Host "  Weekly  : Mondays 9:00 AM      -> $weekly"
Write-Host "  Monthly : 1st of month 9:00 AM -> $monthly"
Write-Host '  Each run saves a date-stamped Excel + HTML report.'
Write-Host '  To change or remove: open Windows "Task Scheduler" and look for'
Write-Host '  "PRG SAMgov Weekly Scan" and "PRG SAMgov Monthly Report".'
Write-Host ''
