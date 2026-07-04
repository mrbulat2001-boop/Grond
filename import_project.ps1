param(
    [Parameter(Mandatory = $true)]
    [string]$ArchivePath
)

$ErrorActionPreference = "Stop"

$archive = (Resolve-Path $ArchivePath).Path
if (-not (Test-Path $archive -PathType Leaf)) {
    throw "Archive not found: $ArchivePath"
}

$workRoot = Join-Path $env:TEMP ("grond-import-" + [guid]::NewGuid().ToString("N"))
$extractDir = Join-Path $workRoot "extracted"
$repoDir = Join-Path $workRoot "Grond"

New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

try {
    Write-Host "Extracting project archive..."
    Expand-Archive -LiteralPath $archive -DestinationPath $extractDir -Force

    $projectFile = Get-ChildItem -Path $extractDir -Filter "project.godot" -File -Recurse | Select-Object -First 1
    if (-not $projectFile) {
        throw "project.godot was not found in the archive."
    }
    $projectRoot = $projectFile.Directory.FullName

    if (Get-Command gh -ErrorAction SilentlyContinue) {
        gh auth setup-git | Out-Null
    }

    Write-Host "Cloning GitHub repository..."
    git clone "https://github.com/mrbulat2001-boop/Grond.git" $repoDir
    if ($LASTEXITCODE -ne 0) { throw "git clone failed." }

    Get-ChildItem -LiteralPath $repoDir -Force |
        Where-Object { $_.Name -ne ".git" } |
        Remove-Item -Recurse -Force

    Write-Host "Copying the complete Godot project..."
    Copy-Item -Path (Join-Path $projectRoot "*") -Destination $repoDir -Recurse -Force
    Get-ChildItem -LiteralPath $projectRoot -Force |
        Where-Object { $_.Name -notin @(".", "..") } |
        ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $repoDir -Recurse -Force
        }

    Push-Location $repoDir
    try {
        git config user.name "Bulat"
        git config user.email "mr.bulat2001@mail.ru"
        git add -A

        $changes = git status --porcelain
        if (-not $changes) {
            Write-Host "Repository already contains the same project."
            exit 0
        }

        git commit -m "Import Helm's Deep 2D RPG v3.0.2"
        if ($LASTEXITCODE -ne 0) { throw "git commit failed." }

        git push origin main
        if ($LASTEXITCODE -ne 0) {
            throw "git push failed. Sign in to GitHub in the browser or run 'gh auth login', then run this script again."
        }
    }
    finally {
        Pop-Location
    }

    Write-Host "Done: https://github.com/mrbulat2001-boop/Grond"
}
finally {
    if (Test-Path $workRoot) {
        Remove-Item -LiteralPath $workRoot -Recurse -Force
    }
}
