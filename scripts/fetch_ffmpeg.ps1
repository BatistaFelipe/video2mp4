$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$ffmpegDir = Join-Path $projectRoot "vendor\ffmpeg"
$vendorDir = Join-Path $ffmpegDir "bin"
$targetExe = Join-Path $vendorDir "ffmpeg.exe"
$targetLicense = Join-Path $ffmpegDir "LICENSE.txt"

if ((Test-Path $targetExe) -and (Test-Path $targetLicense)) {
    Write-Host "[video2mp4] ffmpeg.exe (LGPL) ja presente em $targetExe"
    exit 0
}

New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null

$zipUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-lgpl.zip"
$tempZip = Join-Path $env:TEMP "ffmpeg-master-latest-win64-lgpl.zip"
$tempExtract = Join-Path $env:TEMP "ffmpeg-master-latest-win64-lgpl"

Write-Host "[video2mp4] Baixando ffmpeg (LGPL build) de $zipUrl ..."
Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip

Write-Host "[video2mp4] Extraindo ..."
if (Test-Path $tempExtract) {
    Remove-Item -Recurse -Force $tempExtract
}
Expand-Archive -Path $tempZip -DestinationPath $tempExtract

$ffmpegExe = Get-ChildItem -Path $tempExtract -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
if ($null -eq $ffmpegExe) {
    throw "ffmpeg.exe nao encontrado no zip baixado."
}

$licenseFile = Get-ChildItem -Path $tempExtract -Recurse -Filter "LICENSE.txt" | Select-Object -First 1
if ($null -eq $licenseFile) {
    throw "LICENSE.txt nao encontrado no zip baixado."
}

Copy-Item -Force $ffmpegExe.FullName $targetExe
Copy-Item -Force $licenseFile.FullName $targetLicense

Remove-Item -Force $tempZip
Remove-Item -Recurse -Force $tempExtract

Write-Host "[video2mp4] ffmpeg.exe (LGPL) instalado em $targetExe"
Write-Host "[video2mp4] LICENSE.txt copiado para $targetLicense"
