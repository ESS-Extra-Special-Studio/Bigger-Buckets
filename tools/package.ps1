# Builds the release zip for Bigger Buckets from an allowlist.
#
# Only files tracked by git AND matching $Allow are packed, so logs and local
# test files can never ship. config.txt ships: it is the player's settings
# file, with the default x3. The zip holds one BiggerBuckets folder, ready to
# drop into Content\Paks\~mods.
#   powershell -File tools\package.ps1 -Version 1.0.0
param([Parameter(Mandatory = $true)][string]$Version)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$mod = 'BiggerBuckets'

$Allow = @(
    "^$mod/enabled\.txt$",
    "^$mod/config\.txt$",
    "^$mod/Scripts/[a-z_]+\.lua$"
)
$Docs = @('README.md', 'LICENSE', 'CHANGELOG.md')
$Never = '(^|/)(dev|debug)\.txt$|\.log$|\.tmp$'

$tracked = git ls-files
$files = $tracked | Where-Object { $f = $_; ($Allow | Where-Object { $f -match $_ }).Count -gt 0 }
$bad = $files | Where-Object { $_ -match $Never }
if ($bad) { throw "Refusing to pack: $($bad -join ', ')" }
foreach ($need in "$mod/enabled.txt", "$mod/config.txt", "$mod/Scripts/main.lua") {
    if ($files -notcontains $need) { throw "Missing $need" }
}
if (-not (Select-String -Path "$mod/config.txt" -Pattern '^\s*compost_bucket\s*=\s*3\s*$' -Quiet) -or
    -not (Select-String -Path "$mod/config.txt" -Pattern '^\s*watering_cans\s*=\s*3\s*$' -Quiet)) {
    throw "config.txt is not at the default x3"
}
$dirty = git status --porcelain -- $mod
if ($dirty) { Write-Warning "Uncommitted changes under $mod are packed as they are on disk:`n$dirty" }

$stage = Join-Path $repo "dist\stage-$Version"
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
foreach ($f in $files) {
    $to = Join-Path $stage $f
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $to) | Out-Null
    Copy-Item -LiteralPath (Join-Path $repo $f) -Destination $to
}
foreach ($d in $Docs) { Copy-Item -LiteralPath (Join-Path $repo $d) -Destination (Join-Path $stage "$mod\$d") }

$zip = Join-Path $repo "dist\$mod-$Version.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::Open($zip, 'Create')
try {
    # Forward slashes in entry names, so every unzip tool keeps the folders.
    Get-ChildItem -LiteralPath $stage -Recurse -File -Force | ForEach-Object {
        $name = $_.FullName.Substring($stage.Length + 1).Replace('\', '/')
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $_.FullName, $name) | Out-Null
    }
} finally { $archive.Dispose() }
Remove-Item -Recurse -Force $stage
Write-Output "Packed $($files.Count + $Docs.Count) files into $zip"
