# Avisos de componentes de terceros

> **Borrador (tarea T004).** La lista completa y verificada de todas las dependencias distribuidas en el instalador se genera en la tarea T025 a partir de los metadatos de cada paquete. Lo que sigue incluye los componentes principales y el texto de licencia que exige MarkItDown.

FT Markdown se apoya en el trabajo de otras personas y organizaciones. Este archivo reconoce sus licencias.

## Componentes principales

| Componente | Uso | Licencia |
|---|---|---|
| [MarkItDown](https://github.com/microsoft/markitdown) 0.1.8 | Motor de conversión | MIT (© Microsoft Corporation) |
| [Magika](https://github.com/google/magika) | Detección local del tipo de archivo | Apache-2.0 |
| [ONNX Runtime](https://github.com/microsoft/onnxruntime) | Ejecuta el modelo de Magika | MIT |
| [PySide6 / Qt for Python](https://doc.qt.io/qtforpython-6/) | Interfaz gráfica | LGPL-3.0 |
| Montserrat, Inter, JetBrains Mono | Tipografías (se incorporan en la tarea T017) | SIL Open Font License 1.1 |
| [Lucide](https://lucide.dev) | Íconos (se incorporan en la tarea T017) | ISC |

MarkItDown a su vez incorpora componentes de terceros (por ejemplo, `dwml`, bajo Apache-2.0) descritos en su propio archivo `ThirdPartyNotices.md`, que se distribuye junto con el paquete.

Qt se utiliza bajo los términos de la LGPL-3.0. Las bibliotecas de Qt se incluyen como archivos independientes y reemplazables dentro de la carpeta de instalación. El código fuente de Qt para Python está disponible en https://code.qt.io/cgit/pyside/pyside-setup.git/.

## MarkItDown — texto de la licencia

```
MIT License

Copyright (c) Microsoft Corporation.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE
```
