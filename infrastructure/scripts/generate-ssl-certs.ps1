# Generate SSL certificates for Agent47 development (PowerShell version)
# This script creates self-signed certificates for local development

param(
    [string]$Domain = "agent47.com",
    [int]$Days = 365,
    [int]$KeySize = 2048
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"

Write-Host "🔐 Generating SSL certificates for Agent47 development..." -ForegroundColor $Green

# Create SSL directory if it doesn't exist
$SSL_DIR = Join-Path (Split-Path $PSScriptRoot -Parent) "nginx\ssl"
if (!(Test-Path $SSL_DIR)) {
    New-Item -ItemType Directory -Path $SSL_DIR -Force
}

Set-Location $SSL_DIR

# Check if OpenSSL is available
$openssl = Get-Command openssl -ErrorAction SilentlyContinue
if (!$openssl) {
    Write-Host "❌ OpenSSL not found. Please install OpenSSL or use Git Bash/WSL." -ForegroundColor $Red
    Write-Host "📥 Download OpenSSL from: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor $Yellow
    Write-Host "🔧 Or use Git Bash which includes OpenSSL" -ForegroundColor $Yellow
    exit 1
}

try {
    # Generate private key
    Write-Host "📝 Generating private key..." -ForegroundColor $Yellow
    & openssl genrsa -out agent47.key $KeySize

    # Generate certificate signing request
    Write-Host "📝 Generating certificate signing request..." -ForegroundColor $Yellow
    $subject = "/C=US/ST=CA/L=San Francisco/O=Agent47/OU=Development/CN=$Domain"
    & openssl req -new -key agent47.key -out agent47.csr -subj $subject

    # Generate self-signed certificate
    Write-Host "📝 Generating self-signed certificate..." -ForegroundColor $Yellow
    & openssl x509 -req -days $Days -in agent47.csr -signkey agent47.key -out agent47.crt

    # Generate Diffie-Hellman parameters for better security
    Write-Host "📝 Generating Diffie-Hellman parameters..." -ForegroundColor $Yellow
    & openssl dhparam -out dhparam.pem $KeySize

    # Clean up CSR file
    Remove-Item agent47.csr -ErrorAction SilentlyContinue

    # Set appropriate permissions (Windows)
    $acl = Get-Acl agent47.key
    $acl.SetAccessRuleProtection($true, $false)
    $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("$env:USERNAME", "FullControl", "Allow")
    $acl.SetAccessRule($accessRule)
    Set-Acl agent47.key $acl

    Write-Host "✅ SSL certificates generated successfully!" -ForegroundColor $Green
    Write-Host "📁 Files created in: $SSL_DIR" -ForegroundColor $Green
    Write-Host "   - agent47.crt (certificate)" -ForegroundColor $Green
    Write-Host "   - agent47.key (private key)" -ForegroundColor $Green
    Write-Host "   - dhparam.pem (DH parameters)" -ForegroundColor $Green
    Write-Host ""
    Write-Host "⚠️  Note: These are self-signed certificates for development only." -ForegroundColor $Yellow
    Write-Host "   For production, use certificates from a trusted CA." -ForegroundColor $Yellow
    Write-Host ""
    Write-Host "🚀 You can now start the Agent47 platform with SSL support!" -ForegroundColor $Green

} catch {
    Write-Host "❌ Error generating SSL certificates: $($_.Exception.Message)" -ForegroundColor $Red
    Write-Host "🔧 Make sure OpenSSL is installed and accessible in your PATH" -ForegroundColor $Yellow
    exit 1
}
