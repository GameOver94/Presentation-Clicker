# Build the Presentation Clicker Client as a standalone executable

pyinstaller --noconsole --name PresentationClickerClient `
  --add-data "..\presentation_clicker\client\mqtt_config-template.yaml;presentation_clicker\client" `
  --add-data "..\presentation_clicker\server\mqtt_config-template.yaml;presentation_clicker\server" `
  --paths ".." `
  --hidden-import "presentation_clicker" `
  --hidden-import "presentation_clicker.cli" `
  --hidden-import "presentation_clicker.client" `
  --hidden-import "presentation_clicker.common" `
  --noconfirm `
  .\build_client_cli.py

# Compress the entire build output folder to a zip file and copy to build_scripts
$distFolder = ".\dist\PresentationClickerClient"
$zipPath = "PresentationClickerClient.zip"
$targetZip = Join-Path $PSScriptRoot $zipPath

if (Test-Path $distFolder) {
    if (Test-Path $targetZip) { Remove-Item $targetZip }
    
    # Wait a moment to ensure all files are released
    Start-Sleep -Seconds 2
    
    # Retry logic for compression
    $maxRetries = 3
    $retryCount = 0
    $compressed = $false
    
    while ($retryCount -lt $maxRetries -and -not $compressed) {
        try {
            Compress-Archive -Path $distFolder -DestinationPath $targetZip -Force
            $compressed = $true
            Write-Host "Build and zip complete: $targetZip"
        }
        catch {
            $retryCount++
            Write-Host "Compression attempt $retryCount failed, retrying in 2 seconds..."
            Start-Sleep -Seconds 2
        }
    }
    
    if (-not $compressed) {
        Write-Warning "Zip compression failed after $maxRetries attempts, but build executable is available in: $distFolder"
    }
} else {
    Write-Error "Build failed or folder not found: $distFolder"
    exit 1
}
