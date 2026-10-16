# SPDX-License-Identifier: GPL-2.0-or-later
# Windows 10/11 x64, Windows PowerShell 5.1 or PowerShell 7.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProjectDir = $PSScriptRoot

function Invoke-Checked {
    param([string]$File, [string[]]$Arguments)
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$File failed with exit code $LASTEXITCODE" }
}
function Get-Verified {
    param([string]$Url, [string]$File, [string]$Sha)
    if ((Test-Path -LiteralPath $File) -and ((Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash -eq $Sha)) { return }
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile "$File.part"
    if ((Get-FileHash -LiteralPath "$File.part" -Algorithm SHA256).Hash -ne $Sha) { throw "Download hash mismatch: $Url" }
    Move-Item -LiteralPath "$File.part" -Destination $File -Force
}
function Install-Silent {
    param([string]$File, [string[]]$Arguments)
    $Process = Start-Process -FilePath $File -ArgumentList $Arguments -Wait -PassThru
    if ($Process.ExitCode -notin @(0,3010)) { throw "Installer failed with exit code $($Process.ExitCode)" }
    if ($Process.ExitCode -eq 3010) { Write-Host 'The dependency installer requests a Windows restart after setup.' }
}

if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
    throw 'This setup supports Windows x64 only.'
}
Write-Host 'Ducky One 3 TKL RGB source setup. Nothing will be flashed by setup.'
Write-Host 'Dependencies use unattended installation and their published licenses (THIRD_PARTY.md).'
Write-Host 'Windows may show an administrator/UAC prompt. Existing QMK MSYS installations are reused.'
$DefaultDir = Join-Path $env:USERPROFILE 'DuckyOne3'
$WorkDir = Read-Host "Working directory [$DefaultDir]"
if ([string]::IsNullOrWhiteSpace($WorkDir)) { $WorkDir = $DefaultDir }
$WorkDir = [IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($WorkDir))
if ($WorkDir -match '\s' -or $WorkDir.StartsWith('\\')) { throw 'Use a local absolute directory without whitespace (required by QMK make).' }
New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
$Marker = Join-Path $WorkDir '.ducky-workspace'
if (-not (Test-Path -LiteralPath $Marker) -and @(Get-ChildItem -LiteralPath $WorkDir -Force).Count -gt 0) {
    throw 'Choose an empty directory or an existing Ducky workspace. Existing files were not changed.'
}
New-Item -ItemType File -Path $Marker -Force | Out-Null
$ToolDir = Join-Path $WorkDir 'tools'
New-Item -ItemType Directory -Path $ToolDir -Force | Out-Null
$PythonDir = Join-Path $ToolDir 'python'
$Python = Join-Path $PythonDir 'python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    # Reuse an existing Python 3.12 installation rather than running its maintenance installer.
    foreach ($Root in @('HKCU:\Software\Python\PythonCore\3.12\InstallPath','HKLM:\Software\Python\PythonCore\3.12\InstallPath')) {
        if (Test-Path $Root) {
            $Existing = (Get-ItemProperty $Root).ExecutablePath
            if ($Existing -and (Test-Path -LiteralPath $Existing)) { $Python = $Existing; break }
        }
    }
}
if (-not (Test-Path -LiteralPath $Python)) {
    $Installer = Join-Path $ToolDir 'python-3.12.10-amd64.exe'
    Get-Verified 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' $Installer '67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb'
    Install-Silent $Installer @('/quiet','InstallAllUsers=0','PrependPath=0','Include_test=0','Include_launcher=0','Include_tcltk=1', ('TargetDir="{0}"' -f $PythonDir))
}
Invoke-Checked $Python @('-c','import sys, tkinter; assert sys.version_info[:2] == (3, 12)')
$MsysDir = Join-Path $ToolDir 'qmk-msys'
# QMK MSYS's installer removes an existing version on upgrade. Reuse that version instead.
$UninstallKey = '{52DB9201-A172-4A79-82C3-83B2E8B85FD8}_is1'
foreach ($Root in @('HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall')) {
    $Key = Join-Path $Root $UninstallKey
    if (Test-Path $Key) {
        $Existing = (Get-ItemProperty $Key).InstallLocation
        if ($Existing -and (Test-Path -LiteralPath (Join-Path $Existing 'usr\bin\bash.exe'))) { $MsysDir = $Existing; break }
        throw 'A registered QMK MSYS installation is incomplete. Repair it before rerunning setup; it was not overwritten.'
    }
}
$Bash = Join-Path $MsysDir 'usr\bin\bash.exe'
if (-not (Test-Path -LiteralPath $Bash)) {
    $Installer = Join-Path $ToolDir 'QMK_MSYS-1.12.0.exe'
    Get-Verified 'https://github.com/qmk/qmk_distro_msys/releases/download/1.12.0/QMK_MSYS.exe' $Installer '21df7d55f80870b22121d99867a541cc2a2ed834a28b908d379006a1f7c24c1c'
    # Inno Setup unattended switches. Disable all optional tasks, including driver replacement.
    Install-Silent $Installer @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/TASKS=""',('/DIR="{0}"' -f $MsysDir))
}
$Runtime = Join-Path $WorkDir 'runtime'
Invoke-Checked $Python @('-m','venv',$Runtime)
$RuntimePython = Join-Path $Runtime 'Scripts\python.exe'
Invoke-Checked $RuntimePython @('-m','pip','install','--disable-pip-version-check','-r',(Join-Path $ProjectDir 'requirements.txt'))
Invoke-Checked $RuntimePython @('-m','unittest','discover','-s',(Join-Path $ProjectDir 'tests'),'-v')
Invoke-Checked $RuntimePython @((Join-Path $ProjectDir 'tools\prepare.py'),$WorkDir)
$env:DUCKY_PROJECT = $ProjectDir
$env:DUCKY_WORKSPACE = $WorkDir
$env:MSYSTEM = 'MINGW64'
$env:CHERE_INVOKING = '1'
# No shell expression is passed through PowerShell's legacy native-argument
# quoting. MSYS accepts a forward-slash Windows path as a script filename.
# --login loads QMK's tool PATH; CHERE_INVOKING preserves the caller's directory.
$BuildScript = (Join-Path $ProjectDir 'scripts\build-msys.sh').Replace('\', '/')
Invoke-Checked $Bash @('--login', $BuildScript)
Invoke-Checked $RuntimePython @((Join-Path $ProjectDir 'tools\finalize.py'),$WorkDir)
& $RuntimePython -m pip freeze | Set-Content -Encoding UTF8 (Join-Path $WorkDir 'runtime-packages.txt')
Invoke-Checked $RuntimePython @((Join-Path $ProjectDir 'tools\license_inventory.py'),(Join-Path $WorkDir 'dependency-licenses\runtime'))
# Single-quote literal escaping: paths are data, never executable PowerShell interpolation.
$QuotedPython = $RuntimePython.Replace("'", "''")
$QuotedManager = (Join-Path $ProjectDir 'tools\manage.py').Replace("'", "''")
$QuotedWork = $WorkDir.Replace("'", "''")
$Launcher = "& '$QuotedPython' '$QuotedManager' --workspace '$QuotedWork' @args`r`nexit `$LASTEXITCODE`r`n"
Set-Content -LiteralPath (Join-Path $WorkDir 'Manage-Ducky.ps1') -Value $Launcher -Encoding UTF8
$Cmd = '@echo off' + "`r`n" + 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Manage-Ducky.ps1" %*' + "`r`n" + 'if errorlevel 1 pause' + "`r`n"
Set-Content -LiteralPath (Join-Path $WorkDir 'Manage-Ducky.cmd') -Value $Cmd -Encoding ASCII
$QuotedSettings = (Join-Path $ProjectDir 'tools\settings.py').Replace("'", "''")
$SettingsLauncher = "& '$QuotedPython' '$QuotedSettings' @args`r`nexit `$LASTEXITCODE`r`n"
Set-Content -LiteralPath (Join-Path $WorkDir 'Settings-Ducky.ps1') -Value $SettingsLauncher -Encoding UTF8
$SettingsCmd = '@echo off' + "`r`n" + 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Settings-Ducky.ps1" %*' + "`r`n" + 'if errorlevel 1 pause' + "`r`n"
Set-Content -LiteralPath (Join-Path $WorkDir 'Settings-Ducky.cmd') -Value $SettingsCmd -Encoding ASCII
Write-Host "Settings: $WorkDir\Settings-Ducky.cmd (normal keyboard mode, close VIA)"
Write-Host "Setup completed. Double-click: $WorkDir\Manage-Ducky.cmd"
Write-Host 'Keep this extracted source directory: the launcher uses its tools.'
