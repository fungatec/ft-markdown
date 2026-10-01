# Compila FT Markdown: pruebas -> carpeta con el .exe (PyInstaller) -> instalador (Inno Setup).
# Ejecutar desde cualquier carpeta con:
#   powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
# Opciones: -SkipTests (omite pytest), -SkipInstaller (solo genera la carpeta con el .exe).
# Nota: este archivo es ASCII a proposito (Windows PowerShell 5.1 lee mal los acentos sin BOM).

param(
    [switch]$SkipTests,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "No existe .venv. Ejecuta primero scripts\setup-dev.ps1."
}

$pyVersion = & $python -c "import sys; print('%d.%d' % sys.version_info[:2])"
if ($pyVersion -ne "3.12") {
    throw "El entorno usa Python $pyVersion y el build exige 3.12. Recrea .venv con setup-dev.ps1."
}

$about = Get-Content (Join-Path $root "src\ft_markdown\__about__.py") -Raw
if ($about -notmatch '__version__\s*=\s*"([^"]+)"') { throw "No se pudo leer la version." }
$version = $Matches[1]
Write-Host "== FT Markdown $version ==" -ForegroundColor Cyan

if (-not $SkipTests) {
    Write-Host "[1/4] Ejecutando pruebas ..." -ForegroundColor Cyan
    & $python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Las pruebas fallaron; no se compila." }
} else {
    Write-Host "[1/4] Pruebas omitidas (-SkipTests)." -ForegroundColor Yellow
}

Write-Host "[2/4] Empaquetando con PyInstaller (puede tardar varios minutos) ..." -ForegroundColor Cyan
& $python -m PyInstaller "packaging\ft_markdown.spec" --noconfirm --clean `
    --distpath "dist" --workpath "build\pyinstaller"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller fallo." }

$exe = Join-Path $root "dist\FT Markdown\FT Markdown.exe"
if (-not (Test-Path $exe)) { throw "No se genero $exe." }

Write-Host "[3/4] Autoprueba del ejecutable (convierte un archivo con el motor empaquetado) ..." -ForegroundColor Cyan
$resultado = Join-Path $root "build\selftest.txt"
if (Test-Path $resultado) { Remove-Item $resultado }
$proc = Start-Process -FilePath $exe -ArgumentList @("--selftest", "`"$resultado`"") -Wait -PassThru
if ($proc.ExitCode -ne 0 -or -not (Test-Path $resultado)) {
    $detalle = if (Test-Path $resultado) { Get-Content $resultado -Raw } else { "(sin detalle)" }
    throw "La autoprueba del .exe fallo (codigo $($proc.ExitCode)): $detalle"
}
Write-Host ("    " + (Get-Content $resultado -Raw).Trim()) -ForegroundColor Green

$carpetaMB = [math]::Round(((Get-ChildItem "dist\FT Markdown" -Recurse -File | Measure-Object Length -Sum).Sum / 1MB), 1)
Write-Host "    Tamano de la carpeta de la app: $carpetaMB MB"

if ($SkipInstaller) {
    Write-Host "[4/4] Instalador omitido (-SkipInstaller)." -ForegroundColor Yellow
    return
}

Write-Host "[4/4] Compilando el instalador con Inno Setup ..." -ForegroundColor Cyan
$candidatos = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue | ForEach-Object { $_.Source }),
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
) | Where-Object { $_ -and (Test-Path $_) }
if (-not $candidatos) { throw "No se encontro ISCC.exe. Instala Inno Setup 6 (tarea T002)." }
$iscc = @($candidatos)[0]

& $iscc "/DAppVersion=$version" "packaging\installer.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup fallo." }

$setup = Get-ChildItem "dist-installer" -Filter "FT-Markdown-Setup-*.exe" |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
$setupMB = [math]::Round($setup.Length / 1MB, 1)
Write-Host ""
Write-Host "Listo: $($setup.FullName)  ($setupMB MB)" -ForegroundColor Green
