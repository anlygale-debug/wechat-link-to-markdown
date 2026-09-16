$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'This installer is for Windows.'
}

$packageDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDirectory = Join-Path $packageDirectory 'skill\wechat-link-to-markdown'
if (-not (Test-Path -LiteralPath (Join-Path $sourceDirectory 'SKILL.md'))) {
    $repositoryRoot = Split-Path -Parent $packageDirectory
    $sourceDirectory = Join-Path $repositoryRoot 'skill\wechat-link-to-markdown'
}

if (-not (Test-Path -LiteralPath (Join-Path $sourceDirectory 'SKILL.md'))) {
    throw "Skill files are missing from: $sourceDirectory"
}

foreach ($commandName in @('node', 'npm')) {
    if (-not (Get-Command $commandName -ErrorAction SilentlyContinue)) {
        throw "Missing dependency: $commandName. Install Node.js 20+ and run this installer again."
    }
}

$pythonAvailable = $false
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    $pythonAvailable = ($LASTEXITCODE -eq 0)
}
if (-not $pythonAvailable -and (Get-Command python -ErrorAction SilentlyContinue)) {
    & python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    $pythonAvailable = ($LASTEXITCODE -eq 0)
}
if (-not $pythonAvailable) {
    throw 'Python 3.10+ is required. Install Python, enable its PATH option, and run this installer again.'
}

Write-Host 'Installing OpenCLI 1.8.7...'
& npm install -g '@jackwener/opencli@1.8.7'
if ($LASTEXITCODE -ne 0) {
    throw 'OpenCLI installation failed.'
}

$userProfile = [Environment]::GetFolderPath('UserProfile')
$skillsDirectory = Join-Path $userProfile '.agents\skills'
$targetDirectory = Join-Path $skillsDirectory 'wechat-link-to-markdown'
$resolvedSkillsDirectory = [System.IO.Path]::GetFullPath($skillsDirectory)
$resolvedTargetDirectory = [System.IO.Path]::GetFullPath($targetDirectory)
if (-not $resolvedTargetDirectory.StartsWith($resolvedSkillsDirectory + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Refusing to install outside the user skills directory.'
}

New-Item -ItemType Directory -Force -Path $skillsDirectory | Out-Null
if (Test-Path -LiteralPath $targetDirectory) {
    $backupDirectory = "$targetDirectory.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Write-Host "Existing skill found. Backing it up to: $backupDirectory"
    Move-Item -LiteralPath $targetDirectory -Destination $backupDirectory
}

Copy-Item -LiteralPath $sourceDirectory -Destination $targetDirectory -Recurse

Write-Host ''
Write-Host "Skill installed at: $targetDirectory"
Write-Host 'Next steps:'
Write-Host '1. Install and enable the OpenCLI Chrome extension:'
Write-Host '   https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk'
Write-Host '2. Keep Chrome open and run: opencli doctor'
Write-Host '3. Restart Codex only if the skill does not appear automatically.'
