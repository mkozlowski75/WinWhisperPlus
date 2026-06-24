[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipSigning,
    [string]$CertificateThumbprint = "d7e33e34882d111c4a3eb5cf0175bea39ecf8a29",
    [string]$TimestampServer = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot ".venv-build"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$distDir = Join-Path $repoRoot "dist"
$appDistDir = Join-Path $distDir "WinWhisperPlus"
$appExePath = Join-Path $appDistDir "WinWhisperPlus.exe"
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

function Remove-BuildPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return
    }

    try {
        Remove-Item -Recurse -Force $Path
    } catch {
        throw "Konnte '$Path' nicht loeschen. Bitte pruefen, ob WinWhisperPlus.exe oder ein Prozess aus dem dist-Ordner noch laeuft, und den Build danach erneut starten. Originalfehler: $($_.Exception.Message)"
    }
}

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command,
        [Parameter(Mandatory = $true)]
        [string]$ErrorMessage
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$ErrorMessage Exitcode: $LASTEXITCODE"
    }
}

function Set-CodeSignatureWithPowerShell {
    $normalizedThumbprint = $CertificateThumbprint.Replace(" ", "").ToUpperInvariant()
    $certificate = Get-Item "Cert:\CurrentUser\My\$normalizedThumbprint" -ErrorAction SilentlyContinue
    if (-not $certificate) {
        $certificate = Get-Item "Cert:\LocalMachine\My\$normalizedThumbprint" -ErrorAction SilentlyContinue
    }

    if (-not $certificate) {
        throw "Zertifikat mit Thumbprint $CertificateThumbprint wurde im Benutzer- oder Maschinenzertifikatsspeicher nicht gefunden."
    }
    if (-not $certificate.HasPrivateKey) {
        throw "Zertifikat mit Thumbprint $CertificateThumbprint hat keinen verfuegbaren privaten Schluessel."
    }

    $signature = Set-AuthenticodeSignature `
        -FilePath $appExePath `
        -Certificate $certificate `
        -HashAlgorithm SHA256 `
        -TimestampServer $TimestampServer

    if ($signature.Status -ne "Valid") {
        throw "PowerShell-Signierung ist fehlgeschlagen. Status: $($signature.Status). $($signature.StatusMessage)"
    }
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
        Invoke-NativeCommand {
            py $script:PythonLauncherArg -m venv $venvPath
        } "Virtuelle Build-Umgebung konnte nicht erstellt werden."
    }
    Invoke-NativeCommand {
        & $pythonExe -m pip install --upgrade pip
    } "pip konnte nicht aktualisiert werden."
    Invoke-NativeCommand {
        & $pythonExe -m pip install -r requirements.txt -r requirements-dev.txt
    } "Abhaengigkeiten konnten nicht installiert werden."
}

if (-not $SkipTests) {
    Invoke-Step "Fuehre Tests aus" {
        Invoke-NativeCommand {
            & $pythonExe -m pytest tests
        } "Tests sind fehlgeschlagen."
    }
}

Invoke-Step "Bereinige alte Build-Ausgaben" {
    Remove-BuildPath (Join-Path $repoRoot "build")
    Remove-BuildPath $appDistDir
    Remove-BuildPath $zipPath
}

Invoke-Step "Baue WinWhisperPlus.exe" {
    Invoke-NativeCommand {
        & $pythonExe -m PyInstaller --clean .\WinWhisperPlus.spec
    } "PyInstaller-Build ist fehlgeschlagen."
}

if (-not $SkipSigning) {
    Invoke-Step "Signiere WinWhisperPlus.exe" {
        if (-not (Test-Path $appExePath)) {
            throw "Build-Ausgabe wurde nicht gefunden: $appExePath"
        }
        Set-CodeSignatureWithPowerShell
    }
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
