#Requires -Version 5.0
<#
.SYNOPSIS
  Installs TinyStudioTools.jsx into After Effects ScriptUI Panels (symlink or copy).

.DESCRIPTION
  After Effects only loads ScriptUI Panels from Adobe's Scripts folders under AppData.
  This script links TinyStudioTools.jsx from AERepository into:
    %AppData%\Adobe\After Effects\<version>\Scripts\ScriptUI Panels\

  Symlinks require Windows Developer Mode or an elevated shell; otherwise a file copy is used.

.PARAMETER AeYear
  Marketing year (e.g. 2024). Mapped to Adobe's prefs folder (e.g. 24.0).

.EXAMPLE
  .\install_tinystudio_ae_panel.ps1
  .\install_tinystudio_ae_panel.ps1 -AeYear 2025
#>
param(
    [ValidateRange(2020, 2035)]
    [int]$AeYear = 2024
)

$ErrorActionPreference = "Stop"

$yearToFolder = @{
    "2023" = "23.0"
    "2024" = "24.0"
    "2025" = "25.0"
    "2026" = "26.0"
}

$key = "$AeYear"
if (-not $yearToFolder.ContainsKey($key)) {
    $major = $AeYear - 2000
    if ($major -lt 1 -or $major -gt 99) {
        throw "Unsupported AeYear: $AeYear (could not derive Adobe version folder)."
    }
    $versionFolder = "{0}.0" -f $major
} else {
    $versionFolder = $yearToFolder[$key]
}

$aeRepoRoot = Split-Path $PSScriptRoot -Parent
$scriptsRoot = Join-Path $env:APPDATA "Adobe\After Effects\$versionFolder\Scripts"

function Install-AeScriptLink {
    param(
        [string]$SourceFile,
        [string]$DestDir,
        [string]$DestName
    )
    if (-not (Test-Path -LiteralPath $SourceFile)) {
        throw "Source not found: $SourceFile"
    }
    $sourceResolved = (Resolve-Path -LiteralPath $SourceFile).Path
    New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    $linkPath = Join-Path $DestDir $DestName
    if (Test-Path -LiteralPath $linkPath) {
        Remove-Item -LiteralPath $linkPath -Force
    }
    try {
        New-Item -ItemType SymbolicLink -Path $linkPath -Target $sourceResolved -Force | Out-Null
        Write-Host "Symbolic link created:"
        Write-Host "  $linkPath"
        Write-Host "  -> $sourceResolved"
    } catch {
        Copy-Item -LiteralPath $sourceResolved -Destination $linkPath -Force
        Write-Warning "Symlink failed for ${DestName}: $($_.Exception.Message)"
        Write-Warning "Copied file instead (re-run after pulling repo changes)."
    }
}

$panelSource = Join-Path $aeRepoRoot "scripts\ScriptUI Panels\TinyStudioTools.jsx"
Install-AeScriptLink -SourceFile $panelSource -DestDir (Join-Path $scriptsRoot "ScriptUI Panels") -DestName "TinyStudioTools.jsx"

Write-Host ""
Write-Host "Next: restart After Effects, then open Window -> TinyStudioTools.jsx"
Write-Host "If tools read/write files or network, enable:"
Write-Host "  Edit -> Preferences -> Scripting & Expressions -> Allow Scripts to Write Files and Access Network"
