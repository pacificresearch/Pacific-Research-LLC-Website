# =====================================================================
#  Pacific Research Group LLC - SAM.gov report setup for the Windows PC
# =====================================================================
#  One line, pasted into PowerShell, does everything:
#    iex (irm "https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/main/automation/setup_prg_automation.ps1")
#
#  What it does:
#    1. Uses the existing PRG_SAMgov_Reports folder on your Desktop.
#    2. Downloads the CURRENT matcher from the main branch. (The older setup
#       downloaded from claude/samgov-opportunity-matcher-0a3c2f, frozen in
#       August, before every run. That old copy still carries a dead key and
#       writes a blank report when SAM returns nothing.)
#    3. Tests the saved SAM.gov key; asks for one only if it is missing or
#       SAM rejects it.
#    4. Deletes old blank reports ("0 notices screened").
#    5. Rewrites run_daily / run_weekly / run_monthly so they pull from main
#       and run the daily scan at most once a day. The page that opens is
#       never blank: a failed run shows the last good report with a box on
#       top saying what failed and whether anything needs doing.
#    6. Re-registers the three scheduled tasks and runs one scan now.
#  Re-running it is safe.
# =====================================================================

$ErrorActionPreference = 'Stop'
$mainRaw = 'https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/main/samgov_opportunity_matcher.py'

Write-Host ''
Write-Host '=== PRG SAM.gov report setup ===' -ForegroundColor Cyan

# 1. Folders (GetFolderPath follows OneDrive's Desktop redirection)
$desktop = [Environment]::GetFolderPath('Desktop')
$root    = Join-Path $desktop 'PRG_SAMgov_Reports'
$daily   = Join-Path $root 'Daily'
$weekly  = Join-Path $root 'Weekly'
$monthly = Join-Path $root 'Monthly'
$null = New-Item -ItemType Directory -Force -Path $root, $daily, $weekly, $monthly
Write-Host "  Reports folder: $root" -ForegroundColor Green

# 2. Current matcher from main
$script = Join-Path $root 'samgov_opportunity_matcher.py'
Write-Host '  Downloading the current matcher script...' -ForegroundColor Cyan
Invoke-WebRequest $mainRaw -OutFile $script

# 3. Python packages
Write-Host '  Checking Python packages (requests, openpyxl)...' -ForegroundColor Cyan
try { py -m pip install --quiet --upgrade requests openpyxl }
catch { Write-Host '  (pip step skipped - check that Python is installed)' -ForegroundColor Yellow }

# 4. SAM.gov key, saved for your Windows user so scheduled runs see it too.
#    A saved key is tested once against SAM; a new one is asked for only if
#    the saved one is missing or SAM rejects it (a used-up daily limit is fine).
function Test-SamKey($k) {
    $to   = (Get-Date).ToString('MM/dd/yyyy')
    $from = (Get-Date).AddDays(-1).ToString('MM/dd/yyyy')
    $uri  = "https://api.sam.gov/opportunities/v2/search?limit=1&postedFrom=$from&postedTo=$to&api_key=$k"
    try { $null = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 30; return $true }
    catch {
        $code = 0
        try { $code = [int]$_.Exception.Response.StatusCode } catch { }
        if ($code -eq 401 -or $code -eq 403) { return $false }
        return $true   # 429 (limit used up) or a network blip: the key itself is not the problem
    }
}
$key = [Environment]::GetEnvironmentVariable('SAM_API_KEY', 'User')
$needKey = (-not $key -or $key -like '*PASTE*' -or $key.Trim().Length -lt 20)
if (-not $needKey -and -not (Test-SamKey $key.Trim())) {
    Write-Host '  SAM.gov rejected the saved key (SAM keys expire; get the current one).' -ForegroundColor Yellow
    $needKey = $true
}
while ($needKey) {
    Write-Host '  Get your key at sam.gov -> Workspace -> Account Details -> API Key.'
    $key = (Read-Host '  Paste your SAM.gov API key, then press Enter').Trim()
    if ($key.Length -ge 20 -and (Test-SamKey $key)) {
        [Environment]::SetEnvironmentVariable('SAM_API_KEY', $key, 'User')
        Write-Host '  Key saved.' -ForegroundColor Green
        $needKey = $false
    } else {
        Write-Host '  SAM.gov did not accept that key. Try again.' -ForegroundColor Yellow
    }
}
Write-Host '  SAM.gov key OK.' -ForegroundColor Green
$env:SAM_API_KEY = $key.Trim()

# 5. Remove blank reports so an old blank page can never reopen
$blank = Get-ChildItem $root -Recurse -Filter 'PRG_*Executive_Report_*.html' -ErrorAction SilentlyContinue |
    Where-Object { Select-String -Path $_.FullName -Pattern '\b0 notices screened' -Quiet }
if ($blank) { $blank | Remove-Item; Write-Host "  Deleted $($blank.Count) blank report(s)." -ForegroundColor Green }

# 6. Runner .bat files
$update = "powershell -NoProfile -Command `"try { Invoke-RestMethod '$mainRaw' -OutFile '%~dp0samgov_opportunity_matcher.py' } catch { }`""
$today  = 'for /f %%d in (''powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"'') do set "today=%%d"'

@"
@echo off
setlocal enabledelayedexpansion
$today
set "rep=%~dp0Daily\PRG_Executive_Report_!today!.html"
rem Already ran today with a real report: just open it, do not spend SAM quota again.
if exist "!rep!" (
  findstr /m /c:"PRG-FALLBACK-PAGE" "!rep!" >nul
  if errorlevel 1 (
    start "" "!rep!"
    goto :eof
  )
)
$update
py "%~dp0samgov_opportunity_matcher.py" --days 7 --fast --outdir "%~dp0Daily"
rem Success or not, today's page exists: the real report, or the last good one
rem with a box on top saying what failed and what (if anything) to do.
if exist "!rep!" start "" "!rep!"
"@ | Set-Content (Join-Path $root 'run_daily.bat') -Encoding ASCII

@"
@echo off
$update
py "%~dp0samgov_opportunity_matcher.py" --days 10 --outdir "%~dp0Weekly"
"@ | Set-Content (Join-Path $root 'run_weekly.bat') -Encoding ASCII

@"
@echo off
$update
py "%~dp0samgov_opportunity_matcher.py" --days 90 --outdir "%~dp0Monthly"
"@ | Set-Content (Join-Path $root 'run_monthly.bat') -Encoding ASCII
Write-Host '  Runner files updated to pull from main.' -ForegroundColor Green

# 7. Scheduled tasks, current-user context (no admin needed)
Write-Host '  Registering scheduled tasks...' -ForegroundColor Cyan
$me = whoami
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
$weeklyTrig  = '<CalendarTrigger><StartBoundary>2026-01-01T09:00:00</StartBoundary><Enabled>true</Enabled><ScheduleByWeek><DaysOfWeek><Monday/></DaysOfWeek><WeeksInterval>1</WeeksInterval></ScheduleByWeek></CalendarTrigger>'
$monthlyTrig = '<CalendarTrigger><StartBoundary>2026-01-01T09:00:00</StartBoundary><Enabled>true</Enabled><ScheduleByMonth><DaysOfMonth><Day>1</Day></DaysOfMonth><Months><January/><February/><March/><April/><May/><June/><July/><August/><September/><October/><November/><December/></Months></ScheduleByMonth></CalendarTrigger>'
Register-PRGTask 'PRG SAMgov Daily Morning' (Join-Path $root 'run_daily.bat')   $logonAndDaily
Register-PRGTask 'PRG SAMgov Weekly Scan'    (Join-Path $root 'run_weekly.bat')  $weeklyTrig
Register-PRGTask 'PRG SAMgov Monthly Report' (Join-Path $root 'run_monthly.bat') $monthlyTrig

# 8. Run today's scan now and open it
Write-Host '  Running today''s scan now (a few minutes)...' -ForegroundColor Cyan
& (Join-Path $root 'run_daily.bat')

Write-Host ''
Write-Host '=== Setup complete ===' -ForegroundColor Green
Write-Host "  Daily   : at logon and 6:30 AM, once a day -> $daily (report opens by itself)"
Write-Host "  Weekly  : Mondays 9:00 AM                  -> $weekly"
Write-Host "  Monthly : 1st of the month 9:00 AM         -> $monthly"
Write-Host '  To see today''s report again any time, double-click run_daily.bat.'
Write-Host ''
