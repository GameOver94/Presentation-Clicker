# Build the Presentation Clicker Client as a standalone executable

pyinstaller --noconsole --name PresentationClickerClient `
  ..\presentation_clicker\client\ui_client.py

# Compress the entire build output folder to a zip file and copy to build_scripts
$distFolder = ".\dist\PresentationClickerClient"
$zipPath = "PresentationClickerClient.zip"
$targetZip = Join-Path $PSScriptRoot $zipPath

if (Test-Path $distFolder) {
    if (Test-Path $targetZip) { Remove-Item $targetZip }
    Compress-Archive -Path $distFolder -DestinationPath $targetZip
    Write-Host "Build and zip complete: $targetZip"
} else {
    Write-Error "Build failed or folder not found: $distFolder"
    exit 1
}
