$ErrorActionPreference = "Stop"

$shellRoot = (Resolve-Path (Join-Path $PSScriptRoot ".")).Path
$repoRoot = (Resolve-Path (Join-Path $shellRoot "..\..\..\..")).Path
$wwwRoot = Join-Path $shellRoot "www"

if (Test-Path -LiteralPath $wwwRoot) {
    Remove-Item -LiteralPath $wwwRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $wwwRoot | Out-Null

$webFiles = @(
    "index.html",
    "preview_engine.js",
    "offline_store.js",
    "sw.js",
    "manifest.webmanifest"
)
foreach ($file in $webFiles) {
    Copy-Item -LiteralPath (Join-Path $shellRoot "..\$file") -Destination (Join-Path $wwwRoot $file)
}

$dataDirectories = @("events", "images", "sounds", "fonts", "movies")
$manifest = [System.Collections.Generic.List[object]]::new()
foreach ($directory in $dataDirectories) {
    $source = Join-Path $repoRoot $directory
    $destination = Join-Path $wwwRoot $directory
    if (-not (Test-Path -LiteralPath $source)) { continue }
    Copy-Item -LiteralPath $source -Destination $wwwRoot -Recurse -Force
    Get-ChildItem -LiteralPath $source -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($repoRoot.Length).TrimStart('\','/') -replace '\\','/'
        $manifest.Add([ordered]@{ path = $relative; size = $_.Length })
    }
}

$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $wwwRoot "offline-manifest.json") -Encoding UTF8
Write-Host "Prepared $($manifest.Count) bundled files in $wwwRoot"
