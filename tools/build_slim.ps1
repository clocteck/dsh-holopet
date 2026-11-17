$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$appRoot = Join-Path $repoRoot 'app'
$versionLine = Get-Content (Join-Path $appRoot 'app.info') | Where-Object { $_ -match '^version\s*=' }
$version = ($versionLine -split '=',2)[1].Trim()
$dest = Join-Path $repoRoot "dist/dsh_fish-$version.zip"
New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
Add-Type -AssemblyName System.IO.Compression
$stream = [IO.File]::Open($dest,[IO.FileMode]::Create)
$zip = [IO.Compression.ZipArchive]::new($stream,[IO.Compression.ZipArchiveMode]::Create)
try {
  foreach ($item in Get-ChildItem -LiteralPath $appRoot -Recurse -File) {
    $relative = $item.FullName.Substring($appRoot.Length + 1).Replace('\','/')
    if ($relative -match '(^|/)(skin\.json|settings\.json|.*\.log|.*\.tmp|.*err\.txt)$') { continue }
    $entry = $zip.CreateEntry("dsh_fish/$relative",[IO.Compression.CompressionLevel]::Optimal)
    $source = [IO.File]::OpenRead($item.FullName)
    $target = $entry.Open()
    try { $source.CopyTo($target) } finally { $target.Dispose(); $source.Dispose() }
  }
  foreach ($name in @('LICENSE','CREDITS.md')) {
    $entry = $zip.CreateEntry("dsh_fish/$name",[IO.Compression.CompressionLevel]::Optimal)
    $source = [IO.File]::OpenRead((Join-Path $repoRoot $name))
    $target = $entry.Open()
    try { $source.CopyTo($target) } finally { $target.Dispose(); $source.Dispose() }
  }
} finally { $zip.Dispose(); $stream.Dispose() }
Get-Item $dest | Select-Object FullName,Length
Get-FileHash -Algorithm SHA256 $dest
