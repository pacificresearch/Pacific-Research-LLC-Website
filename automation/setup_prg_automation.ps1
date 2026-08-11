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
#  The daily task runs at LOGON (2-min delay) and at 6:30 AM, and is set to
#  run on battery power — so on a laptop it fires whenever you open and sign
#  in, not just at a clock time you might sleep through. (Windows blocks
#  scheduled tasks on battery by DEFAULT; this setup turns that off, which is
#  the usual reason a laptop "opens and nothing runs.")
# =====================================================================

$ErrorActionPreference = 'Stop'
$branchRaw = 'https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/claude/samgov-opportunity-matcher-0a3c2f/samgov_opportunity_matcher.py'

Write-Host ''
Write-Host '=== PRG SAM.gov automation setup ===' -ForegroundColor Cyan

# 1. Folders — resolve the REAL Desktop (OneDrive Known-Folder-Move aware).
#    $env:USERPROFILE\Desktop is often a hidden legacy folder when OneDrive
#    redirects the Desktop; GetFolderPath returns the one the user can see.
$desktop = [Environment]::GetFolderPath('Desktop')
if (-not $desktop) { $desktop = Join-Path $env:USERPROFILE 'Desktop' }
$root    = Join-Path $desktop 'PRG_SAMgov_Reports'
$daily   = Join-Path $root 'Daily'
$weekly  = Join-Path $root 'Weekly'
$monthly = Join-Path $root 'Monthly'
$null = New-Item -ItemType Directory -Force -Path $root, $daily, $weekly, $monthly
Write-Host "  Reports folder: $root" -ForegroundColor Green

# 1b. If an old install dropped reports in the hidden legacy Desktop folder,
#     move them into the visible one so nothing is lost.
$legacy = Join-Path $env:USERPROFILE 'Desktop\PRG_SAMgov_Reports'
if (($legacy -ne $root) -and (Test-Path $legacy)) {
    Write-Host "  Migrating reports from hidden folder: $legacy" -ForegroundColor Yellow
    Get-ChildItem $legacy -Recurse -File | ForEach-Object {
        $rel  = $_.FullName.Substring($legacy.Length).TrimStart('\')
        $dest = Join-Path $root $rel
        $null = New-Item -ItemType Directory -Force -Path (Split-Path $dest)
        Move-Item $_.FullName $dest -Force
    }
    Remove-Item $legacy -Recurse -Force -ErrorAction SilentlyContinue
}

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
py "%~dp0samgov_opportunity_matcher.py" --days 7 --fast --outdir "%~dp0Daily"
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

# 5. Register scheduled tasks.
#    CRITICAL laptop fixes:
#    - DisallowStartIfOnBatteries / StopIfGoingOnBatteries = FALSE. Windows
#      REFUSES to run scheduled tasks on battery by default and kills any
#      already running when you unplug — the #1 reason a laptop "opens and
#      nothing runs." These two lines are the real fix.
#    - The daily task ALSO triggers AtLogOn (2-min delay for the network),
#      so it runs whenever you open/sign in to the laptop — not just at a
#      fixed clock time you might sleep through. Plus a 6:30 AM trigger with
#      WakeToRun/StartWhenAvailable as a backstop.
Write-Host '  Registering scheduled tasks...' -ForegroundColor Cyan
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$settings.DisallowStartIfOnBatteries = $false
$settings.StopIfGoingOnBatteries     = $false

# Daily: fire at logon (delayed) AND at 6:30 AM — whichever comes first.
$logon = New-ScheduledTaskTrigger -AtLogOn
$logon.Delay = 'PT2M'
$daily630 = New-ScheduledTaskTrigger -Daily -At 6:30am
Register-ScheduledTask -TaskName 'PRG SAMgov Daily Morning' -Force `
    -Action (New-ScheduledTaskAction -Execute $dailyBat) `
    -Trigger $logon, $daily630 `
    -Settings $settings | Out-Null
Register-ScheduledTask -TaskName 'PRG SAMgov Weekly Scan' -Force `
    -Action (New-ScheduledTaskAction -Execute $weeklyBat) `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9:00am) `
    -Settings $settings | Out-Null
# Monthly trigger has no New-ScheduledTaskTrigger equivalent — keep schtasks.
schtasks /Create /TN 'PRG SAMgov Monthly Report' /TR "`"$monthlyBat`"" /SC MONTHLY /D 1 /ST 09:00 /F | Out-Null

# 6. Run one scan now so you have fresh files immediately
Write-Host '  Running a first scan now (~2-3 minutes)...' -ForegroundColor Cyan
py $script --days 7 --fast --outdir $daily

Write-Host ''
Write-Host '=== Setup complete ===' -ForegroundColor Green
Write-Host "  Daily   : at logon + 6:30 AM   -> $daily  (report auto-opens)"
Write-Host "  Weekly  : Mondays 9:00 AM      -> $weekly"
Write-Host "  Monthly : 1st of month 9:00 AM -> $monthly"
Write-Host '  Each run saves a date-stamped Excel + HTML report and'
Write-Host '  self-updates the matcher script before scanning.'
Write-Host '  To change or remove: open Windows "Task Scheduler" and look for'
Write-Host '  the three "PRG SAMgov" tasks.'
Write-Host ''
