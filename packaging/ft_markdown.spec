# -*- mode: python ; coding: utf-8 -*-
# Receta de PyInstaller para FT Markdown (modo "onedir": carpeta con el .exe y sus librerias).
# Se ejecuta a traves de scripts/build.ps1; no hace falta llamarla a mano.
#
# Por que onedir y no onefile: onefile se descomprime en una carpeta temporal en cada arranque
# (lento) y dispara mas falsos positivos de antivirus. Con onedir el instalador ya entrega la
# carpeta lista.

import re
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

RAIZ = Path(SPECPATH).parent
SRC = RAIZ / "src"
NOMBRE = "FT Markdown"

# La version se lee del unico lugar donde se define (src/ft_markdown/__about__.py).
VERSION = re.search(
    r'__version__\s*=\s*"([^"]+)"', (SRC / "ft_markdown" / "__about__.py").read_text("utf-8")
).group(1)

# --- Datos que PyInstaller no detecta solo -------------------------------------------------
# Magika (detector de tipo de archivo de MarkItDown) carga su modelo ONNX desde disco:
# sin estos datos la app abre pero falla al convertir (riesgo alto R1 del plan).
datas = collect_data_files("magika")
datas += collect_data_files("markitdown")
datas += collect_data_files("pdfminer")  # tablas de codificacion de fuentes (cmap)
datas += collect_data_files("pptx")  # plantilla base de python-pptx
datas += collect_data_files("speech_recognition")  # binarios FLAC de la libreria de audio
datas += [(str(RAIZ / "src" / "ft_markdown" / "resources"), "ft_markdown/resources")]
datas += [
    (str(RAIZ / "LICENSE"), "licenses"),
    (str(RAIZ / "THIRD_PARTY_NOTICES.md"), "licenses"),
]

binaries = collect_dynamic_libs("onnxruntime")

# MarkItDown importa cada convertidor dentro de bloques try/except; se fuerza su inclusion.
hiddenimports = collect_submodules("markitdown")
hiddenimports += ["magika", "onnxruntime"]

icono = RAIZ / "src" / "ft_markdown" / "resources" / "icons" / "ft-markdown.ico"

a = Analysis(
    [str(RAIZ / "packaging" / "launcher.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "matplotlib", "pytest", "IPython"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NOMBRE,
    console=False,  # aplicacion de ventana: no abre consola negra
    upx=False,  # UPX provoca falsos positivos de antivirus
    icon=str(icono) if icono.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    upx=False,
    name=NOMBRE,
)
