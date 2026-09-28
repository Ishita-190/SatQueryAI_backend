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

az containerapp up `
    --name $AppName `
    --resource-group $ResourceGroup `
    --location $Location `
    --source $PSScriptRoot `
    --ingress external `
    --target-port 8000

if ($LASTEXITCODE -ne 0) {
    throw "Azure Container Apps deployment failed (az exit code $LASTEXITCODE)."
}