param(
    [Parameter(Mandatory = $true)]
    [string]$VaultName,

    [string]$SecretsFile = (Join-Path $PSScriptRoot "..\azure-key-vault-secrets.production.json"),

    [string]$AppYamlTemplate = (Join-Path $PSScriptRoot "..\app.yaml"),

    [string]$ResolvedAppYaml = (Join-Path $PSScriptRoot "..\app.azure.generated.yaml")
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Find-AzureCli {
    $candidates = [System.Collections.Generic.List[string]]::new()

    foreach ($entry in ($env:PATH -split ";")) {
        $directory = $entry.Trim().Trim('"')
        if (-not [string]::IsNullOrWhiteSpace($directory)) {
            $candidates.Add((Join-Path $directory "az.cmd"))
            $candidates.Add((Join-Path $directory "az.exe"))
        }
    }

    $candidates.Add("C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd")
    $candidates.Add("C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd")

    return $candidates |
        Select-Object -Unique |
        Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
        Select-Object -First 1
}

$resolvedSecretsFile = (Resolve-Path -LiteralPath $SecretsFile).Path
Write-Host "Reading secrets from $resolvedSecretsFile ..."

try {
    $secrets = Get-Content -LiteralPath $resolvedSecretsFile -Raw | ConvertFrom-Json
}
catch {
    throw "Invalid JSON in '$resolvedSecretsFile': $($_.Exception.Message)"
}

$secretProperties = @($secrets.PSObject.Properties)
if ($secretProperties.Count -eq 0) {
    throw "The secrets file '$resolvedSecretsFile' contains no secrets."
}

$az = Find-AzureCli
if (-not $az) {
    throw "Azure CLI ('az') is not installed or is not available on PATH."
}
Write-Host "Using Azure CLI: $az"

Write-Host "Checking Azure login ..."
& $az account show --only-show-errors --output none
if ($LASTEXITCODE -ne 0) {
    throw "Azure CLI is not authenticated. Run 'az login' first."
}

Write-Host "Checking access to Key Vault '$VaultName' ..."
& $az keyvault show --name $VaultName --only-show-errors --output none
if ($LASTEXITCODE -ne 0) {
    throw "Cannot access Key Vault '$VaultName'. Check its name, subscription, and your Key Vault permissions."
}

$secretNumber = 0
foreach ($secret in $secretProperties) {
    $secretNumber++
    $value = [string]$secret.Value
    if ([string]::IsNullOrWhiteSpace($value) -or $value -eq "replace-me") {
        throw "Secret '$($secret.Name)' has no production value."
    }

    Write-Host "Uploading $secretNumber/$($secretProperties.Count): $($secret.Name) ..."
    & $az keyvault secret set `
        --vault-name $VaultName `
        --name $secret.Name `
        --value $value `
        --content-type "former-production-setting" `
        --only-show-errors `
        --output none

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload secret '$($secret.Name)'."
    }
}

Write-Host "Uploaded $($secretProperties.Count) secrets to Key Vault '$VaultName'."

$resolvedYaml = (Get-Content -LiteralPath $AppYamlTemplate -Raw).Replace(
    "YOUR_KEY_VAULT_NAME",
    $VaultName
)
Set-Content -LiteralPath $ResolvedAppYaml -Value $resolvedYaml -Encoding utf8
Write-Host "Generated deployable Container App YAML: $ResolvedAppYaml"
