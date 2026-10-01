param(
    [Parameter(Mandatory)][string]$Archive,
    [Parameter(Mandatory)][string]$Version,
    [string]$CacheRoot = (Join-Path $env:USERPROFILE '.cargo\skia-binaries')
)

$ErrorActionPreference = 'Stop'
$resolvedArchive = (Resolve-Path -LiteralPath $Archive).Path
$actualVersion = (& tar.exe -xOf $resolvedArchive skia-binaries/tag.txt | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $actualVersion -ne $Version) { throw 'Skia binary version does not match' }
$key = (& tar.exe -xOf $resolvedArchive skia-binaries/key.txt | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or (Split-Path -Leaf $resolvedArchive) -ne "skia-binaries-$key.tar.gz") {
    throw 'Skia archive name does not match its build key'
}
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
$template = 'file://' + $CacheRoot.Replace('\', '/') + '/{tag}/skia-binaries-{key}.tar.gz'
Write-Output "Set SKIA_BINARIES_URL to: $template"
