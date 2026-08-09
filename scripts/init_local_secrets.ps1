param(
    [string]$EnvFile = ".env"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
    throw "$EnvFile does not exist. Copy .env.example to .env first."
}

function New-RandomSecret {
    $bytes = New-Object byte[] 48
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    }
    finally {
        $generator.Dispose()
    }
    return ([System.BitConverter]::ToString($bytes)).Replace("-", "").ToLowerInvariant()
}

$requiredNames = @(
    "AIRFLOW_CORE_JWT_SECRET_KEY",
    "AIRFLOW_API_AUTH_JWT_SECRET",
    "AIRFLOW_API_SECRET_KEY"
)

$lines = [System.Collections.Generic.List[string]]::new()
$lines.AddRange([string[]](Get-Content -LiteralPath $EnvFile))
$updated = [System.Collections.Generic.List[string]]::new()

foreach ($name in $requiredNames) {
    $pattern = "^\s*" + [regex]::Escape($name) + "\s*=\s*(.*)$"
    $found = $false
    for ($index = 0; $index -lt $lines.Count; $index++) {
        if ($lines[$index] -match $pattern) {
            $found = $true
            if ([string]::IsNullOrWhiteSpace($Matches[1])) {
                $lines[$index] = "$name=$(New-RandomSecret)"
                $updated.Add($name)
            }
            break
        }
    }
    if (-not $found) {
        $lines.Add("$name=$(New-RandomSecret)")
        $updated.Add($name)
    }
}

$resolvedPath = (Resolve-Path -LiteralPath $EnvFile).Path
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($resolvedPath, $lines, $utf8NoBom)

if ($updated.Count -eq 0) {
    Write-Host "Local Airflow secrets are already configured in $EnvFile."
}
else {
    Write-Host "Generated missing local secrets in ${EnvFile}: $($updated -join ', ')"
}
