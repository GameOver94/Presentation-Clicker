# Build the Presentation Clicker Server as a standalone executable

pyinstaller --noconsole --name PresentationClickerServer `
  ..\presentation_clicker\server\ui_server.py

# Compress the entire build output folder to a zip file and copy to build_scripts
$distFolder = ".\dist\PresentationClickerServer"
$zipPath = "PresentationClickerServer.zip"
$targetZip = Join-Path $PSScriptRoot $zipPath

if (Test-Path $distFolder) {
    if (Test-Path $targetZip) { Remove-Item $targetZip }
    Compress-Archive -Path $distFolder -DestinationPath $targetZip
    Write-Host "Build and zip complete: $targetZip"
} else {
    Write-Error "Build failed or folder not found: $distFolder"
    exit 1
}