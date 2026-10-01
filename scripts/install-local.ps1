param(
    [Parameter(Mandatory)][string]$Archive,
    [Parameter(Mandatory)][string]$Version,
    [string]$CacheRoot = 'C:\Users\Administrator\.cargo\skia-binaries'
)

$ErrorActionPreference = 'Stop'
$resolvedArchive = (Resolve-Path -LiteralPath $Archive).Path
$destination = Join-Path (Join-Path $CacheRoot $Version) (Split-Path -Leaf $resolvedArchive)
New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
Copy-Item -LiteralPath $resolvedArchive -Destination $destination -Force
$checksumFile = "$resolvedArchive.sha256"
if (Test-Path -LiteralPath $checksumFile) {
    Copy-Item -LiteralPath $checksumFile -Destination "$destination.sha256" -Force
    $expected = (Get-Content -LiteralPath $checksumFile -Raw).Split()[0]
    $actual = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected.ToLowerInvariant()) { throw 'Skia binary checksum mismatch' }
}
Write-Output "Installed: $destination"
Write-Output 'Set SKIA_BINARIES_URL to: file:///C:/Users/Administrator/.cargo/skia-binaries/{tag}/skia-binaries-{key}.tar.gz'
