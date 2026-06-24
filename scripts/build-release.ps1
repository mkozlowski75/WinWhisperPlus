[CmdletBinding()]
param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot ".venv-build"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$distDir = Join-Path $repoRoot "dist"
$appDistDir = Join-Path $distDir "WinWhisperPlus"
$zipPath = Join-Path $distDir "WinWhisperPlus.zip"
$pythonVersionArgs = @("-3.14", "-3.13", "-3.12", "-3.11", "-3.10")

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Name"
    & $Action
}

Set-Location $repoRoot

Invoke-Step "Pruefe Python" {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if (-not $py) {
        throw "Python Launcher 'py' wurde nicht gefunden. Bitte Python 3.10 bis 3.14 64-bit installieren."
    }

    $script:PythonLauncherArg = $null
    foreach ($versionArg in $pythonVersionArgs) {
        py $versionArg -c "import sys; raise SystemExit(0 if sys.maxsize > 2**32 else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $script:PythonLauncherArg = $versionArg
            break
        }
    }

    if (-not $script:PythonLauncherArg) {
        throw "Keine passende 64-bit Python-Version gefunden. Bitte Python 3.10 bis 3.14 installieren."
    }

    Write-Host "Verwende Python $script:PythonLauncherArg"
}

Invoke-Step "Erstelle Build-Umgebung" {
    if (-not (Test-Path $pythonExe)) {
        py $script:PythonLauncherArg -m venv $venvPath
    }
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install -r requirements.txt -r requirements-dev.txt
}

if (-not $SkipTests) {
    Invoke-Step "Fuehre Tests aus" {
        & $pythonExe -m pytest tests
    }
}

Invoke-Step "Bereinige alte Build-Ausgaben" {
    if (Test-Path (Join-Path $repoRoot "build")) {
        Remove-Item -Recurse -Force (Join-Path $repoRoot "build")
    }
    if (Test-Path $appDistDir) {
        Remove-Item -Recurse -Force $appDistDir
    }
    if (Test-Path $zipPath) {
        Remove-Item -Force $zipPath
    }
}

Invoke-Step "Baue WinWhisperPlus.exe" {
    & $pythonExe -m PyInstaller --clean .\WinWhisperPlus.spec
}

Invoke-Step "Erstelle ZIP-Paket" {
    if (-not (Test-Path $appDistDir)) {
        throw "Build-Ausgabe wurde nicht gefunden: $appDistDir"
    }
    Compress-Archive -Path (Join-Path $appDistDir "*") -DestinationPath $zipPath -Force
}

Write-Host ""
Write-Host "Release-Paket erstellt:"
Write-Host "  $appDistDir"
Write-Host "  $zipPath"
