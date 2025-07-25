# Kiro IDE Extension Installer
param(
    [string]$ExtensionFile = "mcp-ecosystem-platform-1.0.0.vsix"
)

Write-Host "Extension dosyasi araniyor: $ExtensionFile"

if (-not (Test-Path $ExtensionFile)) {
    Write-Host "HATA: Extension dosyasi bulunamadi: $ExtensionFile" -ForegroundColor Red
    exit 1
}

Write-Host "Extension dosyasi bulundu: $ExtensionFile"

# Kiro extensions dizini
$kiroExtensionsDir = "$env:USERPROFILE\.kiro\extensions"
$targetDir = "$kiroExtensionsDir\mcp-ecosystem.mcp-ecosystem-platform-1.0.0"

# Eski extension'i temizle
if (Test-Path $targetDir) {
    Write-Host "Eski extension temizleniyor..."
    Remove-Item $targetDir -Recurse -Force
}

# Extension'i yukle
Write-Host "Extension yukleniyor..."
try {
    # VSIX dosyasini ZIP olarak ac
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($ExtensionFile, $targetDir)
    
    Write-Host "Extension basariyla yuklendi: $ExtensionFile" -ForegroundColor Green
    Write-Host "Extension $targetDir klasorune kopyalandi."
    
} catch {
    Write-Host "HATA: Extension yuklenemedi: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}