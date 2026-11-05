$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$vendorDir = Join-Path $projectRoot "vendor\ffmpeg\bin"
$targetExe = Join-Path $vendorDir "ffmpeg.exe"

if (Test-Path $targetExe) {
    Write-Host "[video2mp4] ffmpeg.exe ja presente em $targetExe"
    exit 0
}

New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null

$zipUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$tempZip = Join-Path $env:TEMP "ffmpeg-release-essentials.zip"
$tempExtract = Join-Path $env:TEMP "ffmpeg-release-essentials"

Write-Host "[video2mp4] Baixando ffmpeg de $zipUrl ..."
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

Copy-Item -Force $ffmpegExe.FullName $targetExe

Remove-Item -Force $tempZip
Remove-Item -Recurse -Force $tempExtract

Write-Host "[video2mp4] ffmpeg.exe instalado em $targetExe"
