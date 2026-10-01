# FT Markdown

Aplicación de escritorio gratuita para Windows que convierte documentos (PDF, Word, PowerPoint, Excel, páginas web y más) a Markdown. Es un proyecto de [FungaTec](https://github.com/fungatec) construido sobre [MarkItDown](https://github.com/microsoft/markitdown), de Microsoft.

> **Estado:** en desarrollo (v0.1.0, esqueleto del proyecto). Todavía no hay instalador.

## Qué busca ser

Una herramienta limpia y sin complicaciones: arrastras tus archivos, ves el resultado, lo copias o lo guardas. Los formatos locales se convierten sin conexión a internet; las funciones en línea (YouTube, audio, páginas web) se activan solo cuando las usas, y el contenido de tus documentos no sale de tu equipo salvo que tú lo pidas. No incluye publicidad ni telemetría.

## Cómo se desarrolla

El proyecto sigue *Spec-Driven Development*: primero se especifica y se planea, después se construye. Toda la documentación está en [`docs/`](docs/):

- [`docs/sdd/`](docs/sdd/): constitución, especificación, plan técnico y desglose de tareas.
- [`docs/design/`](docs/design/): sistema de diseño y tokens visuales.

## Preparar el entorno de desarrollo (Windows)

Requiere Python 3.12 (la 3.14 no es compatible con una dependencia de MarkItDown; ver el plan técnico).

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-dev.ps1
```

El script crea el entorno virtual `.venv`, instala las dependencias y ejecuta las pruebas.

## Licencia y atribuciones

El código de FT Markdown se distribuye bajo la licencia [MIT](LICENSE).

FT Markdown usa MarkItDown, © Microsoft Corporation, también bajo licencia MIT. Es un proyecto independiente: no está afiliado a Microsoft ni cuenta con su aval. Los avisos de licencia de MarkItDown y del resto de componentes de terceros están en [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

La licencia MIT cubre el código. El nombre «FungaTec», el nombre «FT Markdown» y el logotipo son la identidad de marca de FungaTec y no se otorgan derechos sobre ellos: si haces una versión modificada, cámbiale el nombre y el logotipo.
