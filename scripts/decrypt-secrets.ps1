# decrypt-secrets.ps1 — Descifra secrets\credentials.env.enc en $HOME\.env.spekgen
# Uso (Windows PowerShell): .\scripts\decrypt-secrets.ps1
# El script te pide el password (te lo da Gibran por Signal/WhatsApp).

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Split-Path -Parent $ScriptDir
$EncFile = Join-Path $RepoRoot "secrets\credentials.env.enc"
$OutFile = Join-Path $HOME ".env.spekgen"

if (-not (Test-Path $EncFile)) {
    Write-Error "No existe $EncFile. Repo cloneado completo?"
    exit 1
}

# OpenSSL en Windows: viene con Git for Windows o se instala via choco/winget
$openssl = Get-Command openssl -ErrorAction SilentlyContinue
if (-not $openssl) {
    Write-Error "openssl no instalado. Opciones:`n  - Instalar Git for Windows (incluye openssl en C:\Program Files\Git\usr\bin\)`n  - winget install ShiningLight.OpenSSL`n  - choco install openssl"
    exit 1
}

Write-Host "Descifrando credenciales SPEKGEN."
Write-Host "Password te lo da Gibran por Signal/WhatsApp."
Write-Host ""

# Backup previo si existe
if (Test-Path $OutFile) {
    $bak = "$OutFile.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $OutFile $bak
    Write-Host "Backup previo: $bak"
}

# Decrypt (openssl pide password interactivamente)
& openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -d -in $EncFile -out $OutFile

# Restringir permisos (ACL Windows: solo el usuario actual)
$acl = Get-Acl $OutFile
$acl.SetAccessRuleProtection($true, $false)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    [System.Environment]::UserName, "FullControl", "Allow"
)
$acl.SetAccessRule($rule)
Set-Acl -Path $OutFile -AclObject $acl

$count = (Select-String -Path $OutFile -Pattern '^[A-Z_]' -AllMatches).Matches.Count
Write-Host ""
Write-Host "✓ Descifrado en $OutFile (solo tú lees)"
Write-Host "  $count variables disponibles"
Write-Host ""
Write-Host "Scripts del repo cargan este archivo con python-dotenv automáticamente."
