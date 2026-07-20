# =====================================================================
#  Pacific Research Group LLC — SAM.gov Automation Setup (run once)
# =====================================================================
#  Sets up hands-off scheduled scans that save date-stamped reports to:
#      Desktop\PRG_SAMgov_Reports\Daily     (every day 6:30 AM, last 7 days;
#                                            opens the report in your browser)
#      Desktop\PRG_SAMgov_Reports\Weekly    (Mondays 9:00 AM, last 10 days)
#      Desktop\PRG_SAMgov_Reports\Monthly   (1st of month 9:00 AM, last 90 days)
#
#  Every run re-downloads the latest matcher script first, so scheduled
#  scans always use the newest version automatically. If your Desktop is
#  OneDrive-synced, the reports folder is readable from your phone too.
#
#  Run it once by pasting this into PowerShell:
#    iex (irm "https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/claude/samgov-opportunity-matcher-0a3c2f/automation/setup_prg_automation.ps1")
#
#  NOTE: scheduled scans only run while the PC is on and awake. If it was
#  asleep at the scheduled time, run the .bat in the reports folder by hand
#  (or wake the machine before 6:30 AM — Task Scheduler can also be set to
#  "wake the computer to run this task" in the task's Conditions tab).
# =====================================================================

$ErrorActionPreference = 'Stop'
$branchRaw = 'https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/claude/samgov-opportunity-matcher-0a3c2f/samgov_opportunity_matcher.py'

Write-Host ''
Write-Host '=== PRG SAM.gov automation setup ===' -ForegroundColor Cyan

# 1. Folders
$root    = Join-Path $env:USERPROFILE 'Desktop\PRG_SAMgov_Reports'
$daily   = Join-Path $root 'Daily'
$weekly  = Join-Path $root 'Weekly'
$monthly = Join-Path $root 'Monthly'
$null = New-Item -ItemType Directory -Force -Path $root, $daily, $weekly, $monthly
Write-Host "  Reports folder: $root" -ForegroundColor Green

# 2. Download the latest matcher script
$script = Join-Path $root 'samgov_opportunity_matcher.py'
Write-Host '  Downloading latest matcher script...' -ForegroundColor Cyan
Invoke-WebRequest $branchRaw -OutFile $script

# 3. Make sure Python packages are present
Write-Host '  Installing Python packages (requests, openpyxl)...' -ForegroundColor Cyan
try { py -m pip install --quiet --upgrade requests openpyxl }
catch { Write-Host '  (pip step skipped — check Python is installed)' -ForegroundColor Yellow }

# 4. Runner .bat files (keep the scheduled-task command simple). Each run
#    self-updates the matcher first so it always screens with the newest
#    rubric; if the download fails it falls back to the existing copy.
$update = "powershell -NoProfile -Command `"try { Invoke-RestMethod '$branchRaw' -OutFile '%~dp0samgov_opportunity_matcher.py' } catch { }`""

$dailyBat = Join-Path $root 'run_daily.bat'
@"
@echo off
setlocal enabledelayedexpansion
$update
py "%~dp0samgov_opportunity_matcher.py" --days 7 --outdir "%~dp0Daily"
set "latest="
for /f "delims=" %%f in ('dir /b /od "%~dp0Daily\PRG_Executive_Report_*.html" 2^>nul') do set "latest=%%f"
if defined latest start "" "%~dp0Daily\!latest!"
"@ | Set-Content $dailyBat -Encoding ASCII

$weeklyBat  = Join-Path $root 'run_weekly.bat'
@"
@echo off
$update
py "%~dp0samgov_opportunity_matcher.py" --days 10 --outdir "%~dp0Weekly"
"@ | Set-Content $weeklyBat -Encoding ASCII

$monthlyBat = Join-Path $root 'run_monthly.bat'
@"
@echo off
$update
py "%~dp0samgov_opportunity_matcher.py" --days 90 --outdir "%~dp0Monthly"
"@ | Set-Content $monthlyBat -Encoding ASCII

# 5. Register scheduled tasks
Write-Host '  Registering scheduled tasks...' -ForegroundColor Cyan
schtasks /Create /TN 'PRG SAMgov Daily Morning'  /TR "`"$dailyBat`""   /SC DAILY          /ST 06:30 /F | Out-Null
schtasks /Create /TN 'PRG SAMgov Weekly Scan'    /TR "`"$weeklyBat`""  /SC WEEKLY  /D MON /ST 09:00 /F | Out-Null
schtasks /Create /TN 'PRG SAMgov Monthly Report' /TR "`"$monthlyBat`"" /SC MONTHLY /D 1   /ST 09:00 /F | Out-Null

# 6. Run one scan now so you have fresh files immediately
Write-Host '  Running a first scan now (2-5 minutes)...' -ForegroundColor Cyan
py $script --days 7 --outdir $daily

Write-Host ''
Write-Host '=== Setup complete ===' -ForegroundColor Green
Write-Host "  Daily   : every day 6:30 AM    -> $daily  (report auto-opens)"
Write-Host "  Weekly  : Mondays 9:00 AM      -> $weekly"
Write-Host "  Monthly : 1st of month 9:00 AM -> $monthly"
Write-Host '  Each run saves a date-stamped Excel + HTML report and'
Write-Host '  self-updates the matcher script before scanning.'
Write-Host '  To change or remove: open Windows "Task Scheduler" and look for'
Write-Host '  the three "PRG SAMgov" tasks.'
Write-Host ''
