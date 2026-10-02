# Fase 2 — Plan técnico · FT Markdown

**Versión:** 0.2 · **Fecha:** 2026-10-01 · **Estado:** aprobado · **Implementa:** Especificación v0.2 · **Rige:** Constitución v0.2

## ¿Qué es este paso?

El plan traduce el **qué** de la especificación al **cómo**: qué tecnologías se usan y por qué, cómo se organiza el código, cómo se comunican sus partes y cómo se empaqueta, distribuye y actualiza la app. Cada decisión importante se justifica contra la constitución y se registran las alternativas descartadas, para que dentro de seis meses se entienda por qué se eligió así. El plan todavía no es código: es el plano que el desglose de tareas (fase 3) convierte en pasos pequeños y comprobables.

## 1. Pila tecnológica

| Capa | Elección | Justificación | Alternativas descartadas |
|---|---|---|---|
| Lenguaje | **Python 3.12** (rango admitido 3.10–3.13) | MarkItDown es Python. 3.12 tiene la mayor disponibilidad de paquetes compilados para Windows. **Python 3.14 no sirve:** Magika exige `onnxruntime<=1.20.1` en Windows, versión anterior a Python 3.14 | — |
| Motor | **`markitdown==0.1.8`** desde PyPI con extras `pdf, docx, pptx, xlsx, xls, outlook, audio-transcription, youtube-transcription` | Es la misma versión que tu carpeta (verificado en PyPI); instalarla fijada cumple P1 sin copiar código. `markitdown-main 2/` se queda como referencia y fuente de archivos de prueba | Copiar el código dentro del proyecto: dificulta actualizar y mezcla responsabilidades |
| Interfaz | **PySide6-Essentials** (Qt 6, LGPLv3) | Renderiza Markdown de forma nativa (`QTextBrowser.setMarkdown`), soporta arrastrar y soltar, hilos de fondo (`QThreadPool`), escalado de pantallas de alta densidad, navegación con teclado, accesibilidad de Windows y estilos por QSS generados desde `tokens.json` | CustomTkinter: sin vista previa de Markdown ni arrastrar y soltar nativos y con accesibilidad limitada. Electron/Tauri: obliga a mantener dos lenguajes y un proceso Python aparte |
| Empaquetado | **PyInstaller, modo carpeta (`onedir`)** | Arranque más rápido que `onefile`, menos falsos positivos de antivirus y cumple la LGPL de Qt, porque las DLL quedan reemplazables | Nuitka: compila más lento y es más frágil con pandas/onnxruntime; puede evaluarse más adelante |
| Instalador | **Inno Setup 6**, instalación por usuario | Gratuito y estándar. `PrivilegesRequired=lowest` instala en `%LOCALAPPDATA%\Programs\FT Markdown` sin pedir administrador, lo que permite actualizar sin ventanas de UAC. `AppId` fijo para que cada versión reemplace a la anterior | MSIX: requiere firma obligatoria. WiX: más complejo |
| Actualizaciones | **Módulo propio sobre GitHub Releases** | Releases es gratuito para repositorios públicos y ofrece una API de consulta sin autenticación. El módulo compara versiones con un comparador SemVer propio en `core`, sin dependencias (ver 04-tareas, T016), descarga el instalador y su `.sha256`, verifica y ejecuta | Frameworks de actualización (tufup, PyUpdater): más seguros en teoría, pero añaden infraestructura de llaves desproporcionada para la v1 |
| Datos locales | `platformdirs` → `%APPDATA%\FT Markdown\` (`settings.json`, `history.sqlite`) | Fuera de la carpeta de instalación (P12); `sqlite3` viene con Python | — |
| Credenciales (fase 2) | `keyring` → Administrador de credenciales de Windows | Cumple P4 | — |
| Pruebas y calidad | `pytest`, `pytest-qt`, `ruff` | Pruebas del núcleo sin interfaz y pruebas de interfaz automatizables | — |
| Recursos | Montserrat, Inter y JetBrains Mono (OFL), íconos Lucide (ISC) empaquetados | Sin dependencias de internet para verse bien | — |

## 2. Arquitectura

La app se organiza en cuatro capas con dependencias en una sola dirección (P2). La regla se aplica con inversión de dependencias: `core` no importa ninguna otra capa; `adapters` y `app` importan solo `core`; `ui` importa `app` y `core`; y únicamente la raíz de composición (`__main__.py`) conecta las implementaciones concretas con los casos de uso. El orden del diagrama indica la proximidad al usuario, no la dirección de las importaciones. Una prueba automática (`tests/unit/test_architecture.py`) verifica estas reglas en cada ejecución.

```
┌──────────────────────────────────────────────────────────┐
│ ui/            Ventana, componentes, tema, cadenas         │  PySide6
├──────────────────────────────────────────────────────────┤
│ app/           Casos de uso: cola de conversión, historial,│  Python puro
│                ajustes, conectividad, actualizaciones,     │  + señales Qt
│                componentes descargables                    │
├──────────────────────────────────────────────────────────┤
│ core/          Modelos (Trabajo, Resultado, Capacidad),    │  Python puro
│                catálogo de capacidades, traductor de       │  (sin Qt)
│                errores, interfaz ConversionEngine          │
├──────────────────────────────────────────────────────────┤
│ adapters/      MarkItDownEngine, GitHubReleases, Keyring,  │  Bibliotecas
│                SQLite, descarga de ffmpeg                   │  externas
└──────────────────────────────────────────────────────────┘
```

`core/` no conoce Qt ni MarkItDown: define contratos. `adapters/` los implementa con bibliotecas concretas. Esto tiene una consecuencia directa para la escalabilidad: una futura herramienta de línea de comandos o una integración con FungiDocs reutilizaría `core/`, `app/` y `adapters/` tal cual y solo necesitaría su propia capa de interfaz.

### Estructura de carpetas

```
fungatec-markdown/
├── docs/sdd/ · docs/design/            ← documentación SDD y sistema de diseño
├── src/ft_markdown/
│   ├── __main__.py                     ← punto de entrada
│   ├── __about__.py                    ← versión única de la app
│   ├── core/  models.py · capabilities.py · errors.py · engine.py
│   ├── adapters/  markitdown_engine.py · github_releases.py · history_sqlite.py · ffmpeg_provider.py
│   ├── app/  conversion_queue.py · connectivity.py · settings.py · updater.py · components.py
│   ├── ui/  main_window.py · widgets/ · theme.py (tokens.json → QSS) · strings/es.json
│   └── resources/  fonts/ · icons/ · logo/ · licenses/
├── tests/  unit/ · integration/ · ui/ · fixtures/ (copiados de markitdown-main 2)
├── packaging/  ft_markdown.spec · installer.iss · version_info.txt
├── scripts/  build.ps1 · release.ps1
├── pyproject.toml · README.md · LICENSE · THIRD_PARTY_NOTICES.md
```

## 3. Contratos principales

**`ConversionEngine`** (core) define `convert(source, options) -> ConversionResult`, donde `source` es una ruta o una URL y `options` incluye el idioma (`es-MX` por defecto, FR-010) y los idiomas preferidos para YouTube (`["es", "en"]`, FR-009). `MarkItDownEngine` (adapter) es la **única** clase del proyecto que importa `markitdown` (P1).

**`Capability`** (core) describe cada tipo de entrada con: extensiones, si requiere red, si requiere credenciales y si requiere un componente descargable. El catálogo de capacidades es la tabla §3 de la especificación convertida en datos. La interfaz lo consulta para saber qué habilitar según la conexión (FR-008), y agregar una función futura (por ejemplo, OCR) consiste en registrar una capacidad nueva (P5).

**`ErrorTranslator`** (core) convierte excepciones técnicas en mensajes en español con causa y sugerencia (FR-007). Incluye una regla específica para PDF sin capa de texto: si el resultado está vacío, se informa "PDF sin texto: probablemente es un escaneo; el OCR llegará en una versión futura".

**`ConversionQueue`** (app) ejecuta los trabajos en un grupo de hilos (máximo 2 simultáneos para no saturar la memoria con PDF grandes), emite señales de progreso por trabajo y admite cancelación (FR-005). Un fallo aislado nunca detiene la cola.

**`UpdateService`** (app) consulta `GET /repos/{dueño}/ft-markdown/releases` (lista corta; las preliminares solo cuentan si la versión instalada es preliminar) al arrancar, como máximo una vez cada 24 h, y solo si el usuario no lo desactivó (FR-015). Si hay versión nueva, descarga `FT-Markdown-Setup-X.Y.Z.exe` y su `.sha256` a una carpeta temporal, verifica el hash, espera a que la cola esté vacía, lanza el instalador en modo `/SILENT` y cierra la app; Inno Setup reemplaza los archivos y una entrada `[Run]` del instalador vuelve a abrirla.

**`ComponentManager`** (app) descarga ffmpeg bajo demanda la primera vez que se convierte un MP3 o M4A, previa confirmación, desde una compilación con licencia LGPL, y lo guarda en `%LOCALAPPDATA%\FT Markdown\components\` (FR-016). Así el instalador no carga unos 80–100 MB que la mayoría de usuarios no necesita.

## 4. Trazabilidad requisito → componente

| Requisito | Componentes |
|---|---|
| FR-001, FR-002 | `ui/widgets/drop_zone`, `adapters/markitdown_engine` |
| FR-003, FR-004 | `ui/widgets/preview` (QTextBrowser + vista de código), `app/settings` |
| FR-005, FR-006 | `app/conversion_queue`, `ui/widgets/queue_list` |
| FR-007 | `core/errors` |
| FR-008 | `app/connectivity`, `core/capabilities` |
| FR-009, FR-010 | `adapters/markitdown_engine` (opciones de idioma), `ui/widgets/url_input` |
| FR-011 | `adapters/history_sqlite`, `ui/panels/history` |
| FR-012 | `ui/panels/about`, `resources/licenses` |
| FR-014 | `packaging/installer.iss` |
| FR-015 | `app/updater`, `adapters/github_releases`, `ui/widgets/update_banner` |
| FR-016 | `app/components`, `adapters/ffmpeg_provider` |
| FR-013 (fase 2) | `adapters/keyring_store`, `ui/panels/settings` |

## 5. Flujo de una conversión

El usuario suelta un archivo, y la zona de soltar crea un `ConversionJob`. La cola consulta el catálogo de capacidades: si el formato requiere red y no hay conexión, marca el trabajo como "requiere internet" sin intentarlo. Si no, lo envía a un hilo, donde `MarkItDownEngine` llama a `MarkItDown.convert()` y devuelve un `ConversionResult`. La cola emite la señal de terminado, la interfaz actualiza la fila y muestra la vista previa, y el historial guarda el registro. Si hubo excepción, `ErrorTranslator` produce el mensaje y la fila pasa a "error" con su explicación.

## 6. Compilación, publicación y actualización

**Compilación local** (`scripts/build.ps1`, en tu Windows): crea un entorno virtual, instala dependencias fijadas, corre las pruebas, ejecuta PyInstaller con el archivo `.spec` y compila el instalador con Inno Setup. El `.spec` debe incluir explícitamente los datos de Magika (`collect_data_files("magika")`), las fuentes, los íconos y las licencias. Es el punto técnico más delicado del empaquetado.

**Publicación** (`scripts/release.ps1`): sube la versión en `__about__.py`, genera el `.sha256` del instalador y crea la *release* en GitHub con la CLI `gh`, adjuntando ambos archivos y las notas de la versión. Desde ese momento, todas las copias instaladas detectan la actualización.

**Firma de código.** Un instalador sin firma provoca en Windows la advertencia "Windows protegió su PC" (SmartScreen) hasta que el archivo acumula reputación. Para la v1 se propone publicar sin firma e incluir en la página de descarga cómo continuar ("Más información → Ejecutar de todas formas"). Para versiones posteriores se recomienda solicitar firma gratuita a **SignPath Foundation**, que la ofrece a proyectos de código abierto, aunque exige compilar en un servicio de integración continua como GitHub Actions. Esa migración se planificará como tarea propia.

## 7. Licencias en la distribución

MarkItDown (MIT) y la mayoría de sus dependencias (pandas, pdfminer.six, pdfplumber, mammoth, openpyxl: licencias MIT o BSD) son compatibles con distribuir gratuitamente. PySide6 es LGPLv3: es válido distribuirlo dentro de una app con cualquier licencia siempre que las bibliotecas de Qt sean reemplazables (el modo `onedir` lo garantiza), se incluya su licencia y se indique dónde obtener su código fuente. Las fuentes son OFL y los íconos ISC. ffmpeg no se distribuye en el instalador; se descarga una compilación LGPL bajo demanda. Todo queda listado en `THIRD_PARTY_NOTICES.md` y en el panel "Acerca de". Para FT Markdown se recomienda la licencia **MIT**, coherente con MarkItDown y la más sencilla para quien quiera reutilizar el código (Q-07).

## 8. Riesgos y mitigaciones

| Riesgo | Probabilidad / impacto | Mitigación |
|---|---|---|
| Magika no encuentra su modelo dentro del .exe | Alta / alto | Recolección explícita de datos en el `.spec` y prueba de humo del ejecutable compilado en cada build |
| Los *plugins* de MarkItDown no se cargan en el .exe (`entry_points`) | Alta / medio | Registro explícito de convertidores (P5); la v1 no usa *plugins* externos |
| La transcripción de YouTube deja de funcionar (YouTube bloquea o cambia su interfaz) | Media / bajo | Error traducido y claro; actualizar `youtube-transcript-api` en la siguiente versión |
| El servicio gratuito de voz de Google limita o rechaza audios largos | Media / bajo | Advertencia de duración; transcripción con credenciales en fase 2 |
| Falsos positivos de antivirus con PyInstaller | Media / medio | Modo `onedir`, *bootloader* actualizado, metadatos de versión en el .exe, firma de código a futuro |
| Tamaño mayor al objetivo (NFR-006) | Media / bajo | `PySide6-Essentials` en lugar de PySide6 completo, exclusión de módulos no usados, ffmpeg bajo demanda; se mide en la primera compilación |
| Versión de Python incompatible en la máquina de compilación | Media / alto | `build.ps1` verifica la versión antes de compilar |

## 9. Decisiones resueltas (2026-10-01)

- **Q-05 · Python.** El equipo de compilación tiene Python 3.14.8. Se verificó en PyPI que `onnxruntime 1.20.1`, la versión máxima que Magika 0.6.x admite en Windows, solo publica paquetes para Python 3.10–3.13. Por eso se instala Python 3.12 en paralelo; 3.14 se conserva para otros usos y el proyecto usa su propio entorno virtual con 3.12.
- **Q-06 · GitHub.** Repositorio público `ft-markdown` en la cuenta personal `fungatec` (no es una organización). El código de actualización consulta la misma API pública, que funciona igual para cuentas personales. Se crea antes de T016; entre tanto el control de versiones es un repositorio Git local.
- **Q-07 · Licencia.** Recomendada MIT; pendiente de confirmación (ver tarea T004).

## 10. Primer paso de la fase 3

La primera tarea será una **prueba de concepto técnica** (*spike*): una ventana mínima que convierte un PDF, compilada con PyInstaller e instalada con Inno Setup en tu Windows. Su objetivo es confirmar los dos riesgos altos (Magika empaquetado y compilación local) antes de invertir en la interfaz completa. Si falla, se corrige el plan, no el código.
