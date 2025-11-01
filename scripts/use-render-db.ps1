# Alterna o .env para usar o banco do Render
param(
    [string]$EnvFile = (Join-Path $PSScriptRoot "..\.env")
)

if (!(Test-Path $EnvFile)) {
    Write-Error ".env não encontrado em $EnvFile"
    exit 1
}

$content = Get-Content -Raw -Path $EnvFile

if ($content -match '(?m)^USE_RENDER_DB=') {
    $content = $content -replace '(?m)^USE_RENDER_DB=.*$', 'USE_RENDER_DB=true'
} else {
    $content = $content.TrimEnd() + [Environment]::NewLine + 'USE_RENDER_DB=true' + [Environment]::NewLine
}

Set-Content -Path $EnvFile -Value $content -Encoding UTF8
Write-Host "USE_RENDER_DB=true definido em $EnvFile"
