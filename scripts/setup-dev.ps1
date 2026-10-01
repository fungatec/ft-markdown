# Prepara el entorno de desarrollo de FT Markdown (Python 3.12 + dependencias + pruebas).
# Ejecutar desde la carpeta del proyecto con:
#   powershell -ExecutionPolicy Bypass -File .\scripts\setup-dev.ps1
# Nota: este archivo es ASCII a proposito (Windows PowerShell 5.1 lee mal los acentos sin BOM).

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

py -3.12 --version
if ($LASTEXITCODE -ne 0) {
    throw "No se encontro Python 3.12. Instalalo desde python.org (tarea T001 en docs/sdd/04-tareas.md)."
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creando entorno virtual en .venv ..."
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual." }
}

$python = Join-Path (Get-Location) ".venv\Scripts\python.exe"

Write-Host "Instalando dependencias (la primera vez descarga unos 190 MB) ..."
# Actualizar pip es opcional: si falla (por ejemplo, por una conexion lenta) solo se avisa.
& $python -m pip install --upgrade pip --default-timeout 120 --retries 10
if ($LASTEXITCODE -ne 0) { Write-Warning "No se pudo actualizar pip; se continua con la version actual." }
# Tiempo de espera largo y reintentos: los paquetes grandes (PySide6, 74 MB) fallan con conexiones lentas.
# Lo ya descargado queda en cache, asi que volver a ejecutar el script no empieza de cero.
& $python -m pip install -e ".[dev]" --default-timeout 120 --retries 10
if ($LASTEXITCODE -ne 0) { throw "Fallo al instalar las dependencias. Revisa tu conexion y vuelve a ejecutar el script." }

Write-Host "Ejecutando pruebas ..."
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Alguna prueba fallo." }

Write-Host ""
Write-Host "Listo. Para probar el esqueleto: .\.venv\Scripts\python.exe -m ft_markdown"
