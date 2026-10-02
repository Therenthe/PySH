param(
    [switch]$Install,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ForwardedArgs
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$BundledNode = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
$NodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
$NodeExe = if ($env:PI_SMART_HUB_NODE -and (Test-Path -LiteralPath $env:PI_SMART_HUB_NODE)) {
    (Resolve-Path -LiteralPath $env:PI_SMART_HUB_NODE).Path
} elseif ($NodeCommand) {
    $NodeCommand.Source
} elseif (Test-Path -LiteralPath $BundledNode) {
    $BundledNode
} else {
    throw 'Node.js was not found. Set PI_SMART_HUB_NODE to node.exe or add Node.js to PATH.'
}

$NodeBin = Split-Path -Parent $NodeExe
$NodeRoot = Split-Path -Parent $NodeBin
$NpmCliCandidates = @(
    (Join-Path $NodeRoot 'node_modules\npm\bin\npm-cli.js'),
    (Join-Path $NodeRoot 'npm\bin\npm-cli.js')
)
$PnpmCliCandidates = @(
    (Join-Path $NodeRoot 'node_modules\pnpm\bin\pnpm.mjs'),
    (Join-Path $NodeRoot 'node_modules\pnpm\bin\pnpm.cjs')
)

$PackageManager = $null
$PackageManagerArgs = @()
$Manifest = Get-Content -LiteralPath (Join-Path $ProjectRoot 'package.json') -Raw | ConvertFrom-Json
$NpmCli = $NpmCliCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ($Manifest.packageManager -like 'pnpm@*') {
    $PnpmCli = $PnpmCliCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($PnpmCli) {
        $PackageManager = $NodeExe
        $PackageManagerArgs = @($PnpmCli)
    } else {
        $PnpmCommand = Get-Command pnpm.cmd -ErrorAction SilentlyContinue
        if ($PnpmCommand) {
            $PackageManager = $PnpmCommand.Source
        } else {
            throw 'The package manifest pins pnpm, but no local pnpm CLI was found beside the selected Node.js runtime.'
        }
    }
} elseif ($NpmCli) {
    $PackageManager = $NodeExe
    $PackageManagerArgs = @($NpmCli)
} else {
    throw 'The package manifest does not pin pnpm and no local npm CLI was found beside the selected Node.js runtime.'
}

Push-Location $ProjectRoot
try {
    if ($Install) {
        if ($PackageManagerArgs.Count -gt 0 -and $PackageManagerArgs[0] -match 'pnpm') {
            & $PackageManager @PackageManagerArgs install @ForwardedArgs
        } elseif ($PackageManager -like '*pnpm.cmd') {
            & $PackageManager install @ForwardedArgs
        } else {
            & $PackageManager @PackageManagerArgs install @ForwardedArgs
        }
    } elseif ($PackageManagerArgs.Count -gt 0 -and $PackageManagerArgs[0] -match 'pnpm') {
        & $PackageManager @PackageManagerArgs run dev -- @ForwardedArgs
    } elseif ($PackageManager -like '*pnpm.cmd') {
        & $PackageManager run dev -- @ForwardedArgs
    } else {
        & $PackageManager @PackageManagerArgs run dev -- @ForwardedArgs
    }
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
