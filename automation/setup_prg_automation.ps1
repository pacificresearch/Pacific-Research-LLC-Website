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

# 5. Register scheduled tasks — via schtasks /XML in the CURRENT USER context
#    so NO Administrator elevation is required (Register-ScheduledTask +
#    WakeToRun needs admin and fails with "Access is denied" for normal
#    users). The XML sets the two laptop-critical flags Windows gets wrong by
#    default:
#      DisallowStartIfOnBatteries=false  -> actually run when on battery
#      StopIfGoingOnBatteries=false      -> don't get killed when unplugged
#    The daily task triggers at LOGON (2-min delay so Wi-Fi is up) AND at
#    6:30 AM, so it runs whenever you open/sign in to the laptop. WakeToRun
#    is intentionally omitted (it needs admin and the logon trigger makes it
#    unnecessary).
Write-Host '  Registering scheduled tasks (no admin needed)...' -ForegroundColor Cyan
$me = whoami   # DOMAIN\User or COMPUTER\User

function Register-PRGTask($name, $bat, $triggersXml) {
    $xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>PRG SAM.gov scan</Description></RegistrationInfo>
  <Triggers>$triggersXml</Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$me</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author"><Exec><Command>$bat</Command></Exec></Actions>
</Task>
"@
    $xmlPath = Join-Path $env:TEMP ("prg_task_" + ($name -replace '\W','') + ".xml")
    Set-Content -Path $xmlPath -Value $xml -Encoding Unicode
    schtasks /Create /TN $name /XML "`"$xmlPath`"" /F | Out-Null
    Remove-Item $xmlPath -ErrorAction SilentlyContinue
}

$logonAndDaily = @"
<LogonTrigger><Enabled>true</Enabled><Delay>PT2M</Delay><UserId>$me</UserId></LogonTrigger>
    <CalendarTrigger><StartBoundary>2026-01-01T06:30:00</StartBoundary><Enabled>true</Enabled><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger>
"@
$weeklyTrig = '<CalendarTrigger><StartBoundary>2026-01-01T09:00:00</StartBoundary><Enabled>true</Enabled><ScheduleByWeek><DaysOfWeek><Monday/></DaysOfWeek><WeeksInterval>1</WeeksInterval></ScheduleByWeek></CalendarTrigger>'
$monthlyTrig = '<CalendarTrigger><StartBoundary>2026-01-01T09:00:00</StartBoundary><Enabled>true</Enabled><ScheduleByMonth><DaysOfMonth><Day>1</Day></DaysOfMonth><Months><January/><February/><March/><April/><May/><June/><July/><August/><September/><October/><November/><December/></Months></ScheduleByMonth></CalendarTrigger>'

Register-PRGTask 'PRG SAMgov Daily Morning'  $dailyBat   $logonAndDaily
Register-PRGTask 'PRG SAMgov Weekly Scan'     $weeklyBat  $weeklyTrig
Register-PRGTask 'PRG SAMgov Monthly Report'  $monthlyBat $monthlyTrig

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
