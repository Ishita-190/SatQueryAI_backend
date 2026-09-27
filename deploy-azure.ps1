param(
    [Parameter(Mandatory = $true)]
    [string] $AppName,

    [Parameter(Mandatory = $true)]
    [string] $ResourceGroup,

    [string] $Location = "centralindia"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI (az) is required. Install it and run 'az login' first."
}

$dockerfile = Join-Path $PSScriptRoot "Dockerfile"
if (-not (Test-Path -LiteralPath $dockerfile)) {
    throw "Expected Dockerfile at $dockerfile"
}

az account show --output none
if ($LASTEXITCODE -ne 0) {
    throw "Azure CLI is not signed in. Run 'az login' and retry."
}

$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$buildContext = Join-Path $tempRoot ("SatQueryAI-aca-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $buildContext | Out-Null

try {
    # ACA's local source build expects Dockerfile at the context root. Stage only
    # the runtime files while retaining the paths expected by backend/Dockerfile.
    Copy-Item -LiteralPath $dockerfile -Destination (Join-Path $buildContext "Dockerfile")
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot ".dockerignore") -Destination (Join-Path $buildContext ".dockerignore")
    New-Item -ItemType Directory -Path (Join-Path $buildContext "backend") | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "requirements.txt") -Destination (Join-Path $buildContext "backend\requirements.txt")
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "requirements-models.txt") -Destination (Join-Path $buildContext "backend\requirements-models.txt")
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "app") -Destination (Join-Path $buildContext "backend\app") -Recurse
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "change_detection_training") -Destination (Join-Path $buildContext "backend\change_detection_training") -Recurse
    New-Item -ItemType Directory -Path (Join-Path $buildContext "backend\checkpoints") | Out-Null
    foreach ($checkpoint in @("fusion_model.pt", "optical_sar_water.pt", "best_model.pth")) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot "checkpoints\$checkpoint") -Destination (Join-Path $buildContext "backend\checkpoints\$checkpoint")
    }

    az containerapp up `
        --name $AppName `
        --resource-group $ResourceGroup `
        --location $Location `
        --source $buildContext `
        --ingress external `
        --target-port 8000

    if ($LASTEXITCODE -ne 0) {
        throw "Azure Container Apps deployment failed (az exit code $LASTEXITCODE)."
    }
}
finally {
    $resolvedBuildContext = [System.IO.Path]::GetFullPath($buildContext)
    if (-not $resolvedBuildContext.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove staging directory outside the temporary directory: $resolvedBuildContext"
    }
    Remove-Item -LiteralPath $resolvedBuildContext -Recurse -Force
}
