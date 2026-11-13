#Requires -Version 5.1
<#
Creates a PRIVATE local test-signing key and two files for GitHub repository secrets.
Does not install software, upload files, contact GitHub, or print secret values.
Keep the output folder and password backed up securely. Never commit them.
#>
[CmdletBinding()]
param(
    [string]$OutputDirectory = (Join-Path $env:USERPROFILE 'CDDA-DS-private')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'This helper is for Windows PowerShell. See SIGNING.md for key requirements.'
}

$keytoolCommand = Get-Command keytool -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$keytoolPath = $null
if ($null -ne $keytoolCommand) {
    $keytoolPath = $keytoolCommand.Source
} else {
    $candidates = @()
    if ($env:JAVA_HOME) { $candidates += (Join-Path $env:JAVA_HOME 'bin\keytool.exe') }
    if ($env:ProgramFiles) {
        $candidates += (Join-Path $env:ProgramFiles 'Android\Android Studio\jbr\bin\keytool.exe')
        $jdkRoot = Join-Path $env:ProgramFiles 'Eclipse Adoptium'
        if (Test-Path -LiteralPath $jdkRoot) {
            $candidates += @(Get-ChildItem -LiteralPath $jdkRoot -Directory |
                Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName 'bin\keytool.exe' })
        }
    }
    $keytoolPath = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
}
if (-not $keytoolPath) {
    throw 'Java keytool was not found. Install a Java 17 JDK (for example Eclipse Temurin 17), open a new PowerShell window, then run this helper again. No key was created.'
}

$output = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $output) {
    throw "Output folder already exists: $output. Refusing to overwrite an existing key. Keep and use the original files."
}
# Refuse to place private material inside a Git working tree.
$ancestor = [IO.DirectoryInfo]::new($output)
while ($null -ne $ancestor) {
    if (Test-Path -LiteralPath (Join-Path $ancestor.FullName '.git')) {
        throw 'Choose an output folder outside every Git repository.'
    }
    $ancestor = $ancestor.Parent
}

[IO.Directory]::CreateDirectory($output) | Out-Null
# Restrict this newly created folder to the current Windows user before writing secrets.
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$acl = [Security.AccessControl.DirectorySecurity]::new()
$acl.SetAccessRuleProtection($true, $false)
$rule = [Security.AccessControl.FileSystemAccessRule]::new(
    $sid, [Security.AccessControl.FileSystemRights]::FullControl,
    [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',
    [Security.AccessControl.PropagationFlags]::None,
    [Security.AccessControl.AccessControlType]::Allow
)
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $output -AclObject $acl

$randomBytes = New-Object byte[] 32
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
try { $rng.GetBytes($randomBytes) } finally { $rng.Dispose() }
$password = [BitConverter]::ToString($randomBytes).Replace('-', '')
$previousPassword = [Environment]::GetEnvironmentVariable('CDDA_DS_LOCAL_KEY_PASSWORD', 'Process')
$keyPath = Join-Path $output 'cdda-ds-test.p12'
$certificatePath = Join-Path $output 'cdda-ds-test.cer'
$base64Path = Join-Path $output 'DS_TEST_KEYSTORE_BASE64.txt'
$passwordPath = Join-Path $output 'DS_TEST_STORE_PASSWORD.txt'
$utf8 = [Text.UTF8Encoding]::new($false)

try {
    [Environment]::SetEnvironmentVariable('CDDA_DS_LOCAL_KEY_PASSWORD', $password, 'Process')
    & $keytoolPath -genkeypair -noprompt -storetype PKCS12 -keystore $keyPath `
        -alias cdda-ds-test -keyalg RSA -keysize 3072 -validity 10000 `
        -storepass:env CDDA_DS_LOCAL_KEY_PASSWORD -keypass:env CDDA_DS_LOCAL_KEY_PASSWORD `
        -dname 'CN=CDDA-DS Test Signing,OU=Development,O=CDDA-DS,C=US'
    if ($LASTEXITCODE -ne 0) { throw 'keytool could not generate the test key.' }
    # Save its password immediately so a later certificate-export error cannot strand the key.
    [IO.File]::WriteAllText($passwordPath, $password, $utf8)
    [IO.File]::WriteAllText($base64Path, [Convert]::ToBase64String([IO.File]::ReadAllBytes($keyPath)), $utf8)
    & $keytoolPath -exportcert -keystore $keyPath -storetype PKCS12 -alias cdda-ds-test `
        -storepass:env CDDA_DS_LOCAL_KEY_PASSWORD -file $certificatePath
    if ($LASTEXITCODE -ne 0) { throw 'Certificate export failed. Keep the generated key and password files; do not overwrite them.' }
    $fingerprint = (Get-FileHash -LiteralPath $certificatePath -Algorithm SHA256).Hash.ToLowerInvariant()
    [IO.File]::WriteAllText((Join-Path $output 'CERTIFICATE-SHA256.txt'), $fingerprint, $utf8)
    Write-Host "Private signing files created in: $output"
    Write-Host 'Create these GitHub repository secrets from the correspondingly named text files:'
    Write-Host '  DS_TEST_KEYSTORE_BASE64'
    Write-Host '  DS_TEST_STORE_PASSWORD'
    Write-Host "Public certificate fingerprint: $fingerprint"
    Write-Host 'Back up this private folder securely. Do not upload it to the repository, chat, or an artifact.'
} finally {
    [Environment]::SetEnvironmentVariable('CDDA_DS_LOCAL_KEY_PASSWORD', $previousPassword, 'Process')
    $password = $null
    [Array]::Clear($randomBytes, 0, $randomBytes.Length)
}
