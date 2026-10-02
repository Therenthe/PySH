param(
    [Parameter(Mandatory)][int]$DiskNumber,
    [Parameter(Mandatory)][string]$ExpectedSerial,
    [Parameter(Mandatory)][long]$ExpectedSize,
    [Parameter(Mandatory)][string]$ImagePath,
    [Parameter(Mandatory)][string]$ImageSha256,
    [Parameter(Mandatory)][string]$PublicKeyPath,
    [Parameter(Mandatory)][string]$ImagerPath,
    [Parameter(Mandatory)][string]$LogDirectory,
    [switch]$Write
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
# Defaults to inspection. -Write is allowed only after the user chose this disk.
$taskImage = (Resolve-Path -LiteralPath $ImagePath).Path
$taskPublicKey = (Resolve-Path -LiteralPath $PublicKeyPath).Path
$taskImager = (Resolve-Path -LiteralPath $ImagerPath).Path
$taskLogDir = (Resolve-Path -LiteralPath $LogDirectory).Path
if (!(Get-Item -LiteralPath $taskLogDir).PSIsContainer) { throw 'Log directory required' }
function Get-VerifiedTarget {
    $taskDisk = Get-Disk -Number $DiskNumber
    if ($taskDisk.IsBoot -or $taskDisk.IsSystem -or $taskDisk.BusType -ne 'USB') { throw 'Refusing a system or non-USB disk' }
    if ($taskDisk.SerialNumber.Trim() -ne $ExpectedSerial -or $taskDisk.Size -ne $ExpectedSize) { throw 'Target identity changed' }
    if ($taskDisk.IsReadOnly -or $taskDisk.IsOffline) { throw 'Target is not writable/online' }
    return $taskDisk
}
$taskDisk = Get-VerifiedTarget
$taskImageInfo = Get-Item -LiteralPath $taskImage
if ($taskImageInfo.Length -gt $taskDisk.Size -or $taskImageInfo.Length -lt 1024) { throw 'Image size invalid' }
if ((Get-FileHash -LiteralPath $taskImage -Algorithm SHA256).Hash -ne $ImageSha256) { throw 'Image checksum mismatch' }
$taskSignature = Get-AuthenticodeSignature -LiteralPath $taskImager
if ($taskSignature.Status -ne 'Valid' -or $taskSignature.SignerCertificate.Subject -notmatch 'CN=Raspberry Pi Limited') { throw 'Imager signature invalid' }
$taskKeyLines = [IO.File]::ReadAllLines($taskPublicKey)
if ($taskKeyLines.Count -ne 1 -or $taskKeyLines[0] -notmatch '^ssh-ed25519 [A-Za-z0-9+/]+={0,2}( .*)?$') { throw 'Expected one plain public ed25519 key' }
& "$env:WINDIR/System32/OpenSSH/ssh-keygen.exe" -l -f $taskPublicKey
if ($LASTEXITCODE -ne 0) { throw 'Public key validation failed' }
$taskPartitions = @(Get-Partition -DiskNumber $DiskNumber)
foreach ($taskPartition in $taskPartitions) {
    foreach ($taskAccessPath in @($taskPartition.AccessPaths)) {
        if ($taskAccessPath -and $taskAccessPath -notmatch '^[A-Za-z]:\\$' -and !$taskAccessPath.StartsWith('\\?\Volume{')) { throw 'Refusing a target with directory mount points' }
    }
}
$taskLetters = @($taskPartitions | Where-Object DriveLetter | ForEach-Object { "$($_.DriveLetter):" })
foreach ($taskSource in @($taskImage,$taskPublicKey,$taskImager,$taskLogDir)) {
    if ($taskLetters -contains ([IO.Path]::GetPathRoot($taskSource).TrimEnd('\'))) { throw 'A source or log lives on the target disk' }
    $taskParent = Get-Item -LiteralPath $taskSource
    while ($taskParent) {
        if ($taskParent.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refusing a source/log path through a junction or symlink' }
        $taskParent = $(if ($taskParent -is [IO.FileInfo]) { $taskParent.Directory } else { $taskParent.Parent })
    }
}
$taskMbr = New-Object byte[] 512
$taskImageStream = [IO.File]::OpenRead($taskImage)
try { if ($taskImageStream.Read($taskMbr,0,512) -ne 512) { throw 'Incomplete MBR' } } finally { $taskImageStream.Dispose() }
if ($taskMbr[510] -ne 85 -or $taskMbr[511] -ne 170 -or $taskMbr[450] -ne 12 -or $taskMbr[466] -ne 131) { throw 'Unexpected partition layout' }
$taskBootOffset = [long][BitConverter]::ToUInt32($taskMbr,454)*512
$taskBootSize = [long][BitConverter]::ToUInt32($taskMbr,458)*512
if ($taskBootOffset -ne 8388608 -or $taskBootSize -ne 268435456) { throw 'Unexpected boot partition bounds' }
$taskPlan = [ordered]@{ disk=$DiskNumber; name=$taskDisk.FriendlyName; serial=$ExpectedSerial; bytes=$ExpectedSize; image=$taskImage; sha256=$ImageSha256; action= $(if ($Write) {'WRITE AND VERIFY'} else {'INSPECTION ONLY'}) }
$taskPlan | ConvertTo-Json
if (!$Write) { return }
$taskAdmin = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (!$taskAdmin.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Administrator token required for writing' }
$null = Get-VerifiedTarget
$taskDevice = "\\.\PhysicalDrive$DiskNumber"
# Keep default read-back verification. Do not eject before public-key provisioning.
$taskArguments = @('--cli','--disable-eject','--sha256',$ImageSha256,'"'+$taskImage+'"',$taskDevice)
$taskWriter = Start-Process -FilePath $taskImager -ArgumentList $taskArguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $taskLogDir 'flash.stdout.log') -RedirectStandardError (Join-Path $taskLogDir 'flash.stderr.log')
if ($taskWriter.ExitCode -ne 0) { throw "Imager failed: $($taskWriter.ExitCode); inspect flash.stderr.log" }
$null = Get-VerifiedTarget
Update-HostStorageCache
$taskDeadline = (Get-Date).AddSeconds(30)
do {
    $taskBoot = @(Get-Partition -DiskNumber $DiskNumber | Where-Object { $_.Offset -eq $taskBootOffset -and $_.Size -eq $taskBootSize })
    if ($taskBoot.Count -eq 1) { break }
    Start-Sleep -Seconds 1
    Update-HostStorageCache
} while ((Get-Date) -lt $taskDeadline)
if ($taskBoot.Count -ne 1) { throw 'Written image verified, but boot partition cannot be identified; no key copied' }
if (!$taskBoot[0].DriveLetter) {
    $taskFreeLetter = @('P','Q','R','S','T') | Where-Object { !(Get-Volume -DriveLetter $_ -ErrorAction SilentlyContinue) } | Select-Object -First 1
    if (!$taskFreeLetter) { throw 'No free drive letter for recovery provisioning' }
    $taskBoot[0] | Set-Partition -NewDriveLetter $taskFreeLetter
    $taskBoot = @(Get-Partition -DiskNumber $DiskNumber | Where-Object { $_.Offset -eq $taskBootOffset -and $_.Size -eq $taskBootSize })
}
$taskVolume = Get-Volume -DriveLetter $taskBoot[0].DriveLetter
if ($taskVolume.FileSystem -ne 'FAT32') { throw 'Boot volume is not FAT32' }
$taskBootPath = "$($taskBoot[0].DriveLetter):\"
if (!(Test-Path -LiteralPath (Join-Path $taskBootPath 'cmdline.txt')) -or !(Test-Path -LiteralPath (Join-Path $taskBootPath 'config.txt'))) { throw 'Boot files missing' }
$taskBootKey = Join-Path $taskBootPath 'pysh-recovery.pub'
if (Test-Path -LiteralPath $taskBootKey) { throw 'Refusing to overwrite an existing provisioning key' }
Copy-Item -LiteralPath $taskPublicKey -Destination $taskBootKey
$taskKeyStream = [IO.File]::Open($taskBootKey,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
try { $taskKeyStream.Flush($true) } finally { $taskKeyStream.Dispose() }
if ((Get-FileHash -LiteralPath $taskBootKey).Hash -ne (Get-FileHash -LiteralPath $taskPublicKey).Hash) { throw 'Provisioned public key checksum mismatch' }
$taskPlan['result'] = 'Image write/read-back verified; PUBLIC recovery key copied and flushed. Use Windows safe removal before unplugging. Physical boot remains OPEN.'
$taskPlan | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $taskLogDir 'flash-result.json')
$taskPlan | ConvertTo-Json
