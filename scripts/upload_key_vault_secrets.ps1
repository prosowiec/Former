param(
    [Parameter(Mandatory = $true)]
    [string]$VaultName,

    [string]$SecretsFile = (Join-Path $PSScriptRoot "..\azure-key-vault-secrets.production.json"),

    [string]$AppYamlTemplate = (Join-Path $PSScriptRoot "..\app.yaml"),

    [string]$ResolvedAppYaml = (Join-Path $PSScriptRoot "..\app.azure.generated.yaml")
)

$ErrorActionPreference = "Stop"
$resolvedSecretsFile = (Resolve-Path -LiteralPath $SecretsFile).Path
$secrets = Get-Content -LiteralPath $resolvedSecretsFile -Raw | ConvertFrom-Json

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI ('az') is not installed or is not available on PATH."
}

az account show --only-show-errors 1>$null
if ($LASTEXITCODE -ne 0) {
    throw "Azure CLI is not authenticated. Run 'az login' first."
}

foreach ($secret in $secrets.PSObject.Properties) {
    $value = [string]$secret.Value
    if ([string]::IsNullOrWhiteSpace($value) -or $value -eq "replace-me") {
        throw "Secret '$($secret.Name)' has no production value."
    }

    az keyvault secret set `
        --vault-name $VaultName `
        --name $secret.Name `
        --value $value `
        --content-type "former-production-setting" `
        --only-show-errors `
        --output none

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload secret '$($secret.Name)'."
    }
    Write-Host "Uploaded $($secret.Name)"
}

$secretCount = @($secrets.PSObject.Properties).Count
Write-Host "Uploaded $secretCount secrets to Key Vault '$VaultName'."

$resolvedYaml = (Get-Content -LiteralPath $AppYamlTemplate -Raw).Replace(
    "YOUR_KEY_VAULT_NAME",
    $VaultName
)
Set-Content -LiteralPath $ResolvedAppYaml -Value $resolvedYaml -Encoding utf8
Write-Host "Generated deployable Container App YAML: $ResolvedAppYaml"
