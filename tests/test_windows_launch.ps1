# SPDX-License-Identifier: GPL-2.0-or-later
# Run with Windows PowerShell 5.1 or PowerShell 7; needs bash (Git Bash is enough).
param([string]$BashPath = 'bash')
$ErrorActionPreference = 'Stop'
$Project = Split-Path $PSScriptRoot -Parent
$Tokens = $null
$Errors = $null
$Ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $Project 'Setup-Windows.ps1'), [ref]$Tokens, [ref]$Errors)
if ($Errors) { throw ($Errors | Out-String) }
$Function = $Ast.Find({ param($Node) $Node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $Node.Name -eq 'Invoke-Checked' }, $true)
. ([scriptblock]::Create($Function.Extent.Text))
$Calls = @($Ast.FindAll({ param($Node) $Node -is [System.Management.Automation.Language.CommandAst] -and $Node.GetCommandName() -eq 'Invoke-Checked' -and $Node.Extent.Text -match '\$Bash\b' }, $true))
if ($Calls.Count -ne 1 -or $Calls[0].Extent.Text -match "'-lc'|'-c'") { throw 'Expected exactly one direct bash script invocation, without -c.' }
$TempDir = Join-Path ([IO.Path]::GetTempPath()) ('ducky-launch-' + [guid]::NewGuid().ToString() + ' (with spaces)')
New-Item -ItemType Directory -Path $TempDir | Out-Null
try {
    $ScriptPath = Join-Path $TempDir 'entry script.sh'
    # Use LF explicitly, without BOM or PowerShell's platform newline conversion.
    [IO.File]::WriteAllText($ScriptPath, "#!/usr/bin/env bash`nprintf '%s' DUCKY_LAUNCH_OK`n", (New-Object Text.UTF8Encoding($false)))
    $Bash = $BashPath
    $BuildScript = $ScriptPath.Replace('\', '/')
    $Result = & ([scriptblock]::Create($Calls[0].Extent.Text))
    if (($Result -join "`n") -notmatch 'DUCKY_LAUNCH_OK') { throw 'Bash did not execute the script file.' }
    Write-Output 'PASS: direct PowerShell-to-Bash script invocation, path with spaces and parentheses.'
} finally {
    [IO.Directory]::Delete($TempDir, $true)
}
