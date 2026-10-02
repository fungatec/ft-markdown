# Fase 3 — Desglose de tareas · FT Markdown v1.0

**Versión:** 0.2 · **Fecha:** 2026-10-01 · **Estado:** en revisión · **Implementa:** Plan v0.2

## ¿Qué es este paso?

El desglose convierte el plan en tareas pequeñas, ordenadas y verificables. Cada tarea tiene un identificador (`T001`), indica qué requisito cumple, quién la ejecuta y cuál es su criterio de terminado. Así el avance es medible ("van 14 de 29") y, si algo falla, se sabe exactamente dónde. Las tareas del núcleo siguen el enfoque *prueba primero*: se escribe la prueba que define el comportamiento esperado y después el código que la hace pasar.

**Convenciones.** `[P]` significa que la tarea puede hacerse en paralelo con las demás `[P]` de su bloque. **Quién:** *Claude* escribe el código en la carpeta del proyecto y prueba la parte que no depende de Windows; *Tú* ejecutas lo que exige Windows o tus cuentas (compilar, instalar, publicar). Los **puntos de control** (◆) son revisiones obligatorias antes de continuar.

## Bloque A — Preparación del entorno

| ID | Tarea | Quién | Terminado cuando… |
|---|---|---|---|
| T001 | Instalar Python 3.12 en paralelo a 3.14 | Tú | `py -3.12 --version` responde `Python 3.12.x` |
| T002 | Instalar Inno Setup 6 y GitHub CLI; iniciar sesión con `gh auth login` | Tú | `iscc /?` y `gh auth status` responden sin error |
| T003 | Crear el repositorio público `ft-markdown` en la cuenta `fungatec` (**pospuesto hasta antes de T016**: el bloque B no lo necesita; mientras tanto se usa `git init` local) | Tú | `gh repo view fungatec/ft-markdown` responde |

## Bloque B — Prueba de concepto (*spike*)

| ID | Tarea | Requisito | Quién | Terminado cuando… |
|---|---|---|---|---|
| T004 | Esqueleto del proyecto: `pyproject.toml` con dependencias fijadas, estructura de carpetas del plan, `LICENSE`, `.gitignore`, `README.md` | P1, P10 | Claude | La estructura coincide con el plan §2 |
| T005 | Ventana mínima PySide6 que convierte un PDF elegido con un botón y muestra el Markdown | FR-001, FR-002 | Claude | Funciona con `py -3.12 -m ft_markdown` en tu Windows |
| T006 | `ft_markdown.spec` de PyInstaller (con datos de Magika) y `scripts/build.ps1` | Plan §6 | Claude | El script corre de principio a fin sin errores |
| T007 | `installer.iss` mínimo (instalación por usuario, acceso en menú Inicio, desinstalador) | FR-014 | Claude | Inno Setup compila el instalador |
| T008 | Compilar, instalar y convertir `test.pdf` desde la app instalada; anotar tamaño del instalador y de la instalación | NFR-001, NFR-006 | Tú | La app instalada convierte el PDF en un Windows donde no se use Python |

◆ **Punto de control 1.** Si T008 falla, se corrige el plan (fase 2) antes de seguir. Este punto confirma los dos riesgos altos del plan: Magika empaquetado y compilación local.

## Bloque C — Núcleo (prueba primero)

| ID | Tarea | Requisito | Quién | Terminado cuando… |
|---|---|---|---|---|
| T009 | Modelos (`ConversionJob`, `ConversionResult`, `Capability`) y catálogo de capacidades a partir de la tabla §3 de la especificación | FR-002, FR-008, P5 | Claude | Pruebas unitarias en verde |
| T010 [P] | `ErrorTranslator` con mensajes en español, incluida la regla "PDF sin texto" | FR-007 | Claude | Cada excepción de MarkItDown tiene prueba y mensaje |
| T011 | `MarkItDownEngine` con opciones de idioma (`es-MX`, `["es", "en"]`) | FR-002, FR-009, FR-010, P1 | Claude | Los 25 archivos de prueba locales producen Markdown; prueba de que no hay tráfico de red |
| T012 [P] | Ajustes (`settings.json`) e historial (`history.sqlite`) en `%APPDATA%\FT Markdown` | FR-006, FR-011, P12 | Claude | Pruebas en verde; datos fuera de la carpeta de instalación |

## Bloque D — Servicios de aplicación

| ID | Tarea | Requisito | Quién | Terminado cuando… |
|---|---|---|---|---|
| T013 | `ConversionQueue`: hilos, progreso, cancelación, aislamiento de fallos | FR-005 | Claude | Un archivo dañado en un lote de 10 no detiene los otros 9 |
| T014 [P] | `ConnectivityMonitor` | FR-008 | Claude | Detecta el cambio en línea / sin conexión en menos de 10 s |
| T015 [P] | `ComponentManager` para ffmpeg bajo demanda (LGPL) con confirmación | FR-016 | Claude | Descarga, verifica y registra ffmpeg; un MP3 se transcribe |
| T016 | `UpdateService` + adaptador de GitHub Releases, verificación SHA-256, límite de una consulta cada 24 h | FR-015, P11 | Claude | Pruebas con respuestas simuladas de versión nueva, igual y antigua |

◆ **Punto de control 2.** Revisión del núcleo y los servicios funcionando sin interfaz.

## Bloque E — Interfaz

| ID | Tarea | Requisito | Quién | Terminado cuando… |
|---|---|---|---|---|
| T017 | `theme.py`: `tokens.json` → QSS para los temas oscuro y claro; fuentes empaquetadas; `strings/es.json` | P6, P8 | Claude | Cambiar un token cambia la interfaz sin tocar otro archivo |
| T018 | Ventana principal de dos columnas, zona de soltar y botón "Examinar"; `closeEvent` llama a `shutdown()` de la cola y del monitor | FR-001 | Claude | Arrastrar y examinar funcionan, también con teclado; cerrar con una conversión en curso no deja hilos ni falla |
| T019 | Lista de cola con los cinco estados (ícono + texto + color) | FR-005, FR-007 | Claude | Los cinco estados visibles y legibles en ambos temas |
| T020 | Vista previa fuente / renderizada; copiar; guardar `.md` sin sobrescribir sin preguntar; carpeta de salida | FR-003, FR-004, FR-006 | Claude | Criterios de HU-2 cumplidos |
| T021 [P] | Entrada de URL / YouTube y selector de idioma para audio; acciones en línea desactivadas sin conexión | FR-008, FR-009, FR-010 | Claude | Criterios de HU-5 y HU-6 cumplidos |
| T022 [P] | Paneles de historial, ajustes (incluido desactivar actualizaciones) y "Acerca de" | FR-011, FR-012, FR-015 | Claude | Paneles navegables con teclado |
| T023 | Franja de aviso de actualización con sus cuatro estados | FR-015 | Claude | Nunca bloquea la ventana ni interrumpe una conversión |
| T024 | Revisión de accesibilidad con la lista §8 del sistema de diseño | NFR-003 | Claude + Tú | Todos los puntos marcados |

◆ **Punto de control 3.** Pruebas la app completa en tu Windows y das retroalimentación de diseño.

## Bloque F — Empaquetado, publicación y verificación

| ID | Tarea | Requisito | Quién | Terminado cuando… |
|---|---|---|---|---|
| T025 | `THIRD_PARTY_NOTICES.md` y licencias incluidas en la app | P9, NFR-007 | Claude | Cada dependencia distribuida aparece con su licencia |
| T026 | Instalador final: `AppId` fijo, `[Run]` para reabrir tras actualizar, conservación de datos al desinstalar | FR-014, P12 | Claude | Instalar, actualizar y desinstalar sin perder ajustes |
| T027 | `scripts/release.ps1`: versión, SHA-256 y `gh release create` | FR-015 | Claude | Publica una versión de prueba en el repositorio |
| T028 | Prueba de actualización de extremo a extremo: instalar `1.0.0-beta.1`, publicar `1.0.0-beta.2`, actualizar desde la app | FR-015, HU-10 | Tú | La app se actualiza sola y conserva el historial |
| T029 | Verificación final contra los criterios de éxito §9 de la especificación, hecha por un revisor independiente que no escribió el código | P7 | Claude (revisor aparte) + Tú | Informe sin fallos críticos |

◆ **Punto de control 4.** Publicación de FT Markdown **v1.0.0**.

## Progreso

| Tarea | Estado | Commit |
|---|---|---|
| T001, T002 | Hecho | — |
| T003 | Pospuesto (antes de T016) | — |
| T004, T005 | Hecho | `a9d5927` |
| T006, T007 | Hecho | `e7c836f` |
| T008 | Hecho: instalador 95,7 MB; ◆ Punto de control 1 superado | — |
| T009, T010 | Hecho | `f7845dc` |
| T011 | Hecho | `92e63c1` |
| T012 | Hecho | `ef04744` |
| T013 | Hecho | `125f8d0` |
| T014 | Hecho | `2e57df8`, `19382dd` |
| T015 | Hecho | `0898fc5` |
| Ajuste T013/T014 (cierre ordenado) | Hecho | `ed8c0c1` |
| T016 | Hecho | `0437f67` |

**Correcciones al plan descubiertas al implementar**
- FR-010: MarkItDown 0.1.8 no permite elegir el idioma del audio (transcribe siempre en inglés). El audio se atiende en `adapters/audio_transcriber.py`; YouTube sí admite idiomas por parámetro.
- Historial (FR-011): guarda ruta, título, estado y fecha; no el contenido (P4).
- Cancelación (FR-005): MarkItDown no se puede interrumpir a mitad de un archivo. Los trabajos pendientes se cancelan al instante; el que está convirtiendo termina y su resultado se descarta (queda CANCELLED). La cola vive en `app/conversion_queue.py` con `QThreadPool` (máx. 2 simultáneos).
- Conectividad (FR-008, P11, NFR-004): `app/connectivity.py` nace detenido y no abre ningún socket hasta `start()`. Activo, comprueba de inmediato y luego cada 5 s en un hilo aparte (sonda TCP de 3 s a 1.1.1.1 y 8.8.8.8, sin enviar datos) y avisa solo cuando el estado cambia. `stop()` devuelve `is_online` a `None` y descarta la consulta en curso. **T021 debe llamar `start()` al mostrar el panel de URL/YouTube/audio y `stop()` al ocultarlo.** T022 documentará esas dos direcciones en el panel de privacidad.
- Cierre ordenado (ajuste a T013/T014): una cola o un monitor vivos al terminar provocaban un *access violation* intermitente (un hilo emitía una señal sobre un objeto Qt ya destruido; reproducido bajo carga). `ConversionQueue.shutdown(timeout_ms=5000)` y `ConnectivityMonitor.shutdown(timeout_ms=4000)` cancelan, esperan con plazo y, desde entonces, ningún hilo toca objetos Qt, aunque termine después del plazo (devuelven `False` si no terminó a tiempo). `ConnectivityMonitor.stop()` **no espera** a la sonda, para no congelar la interfaz al ocultar el panel; el cierre ordenado es `shutdown()`. Los tests usan `queue_factory` y `monitor_factory` (`tests/conftest.py`), que cierran lo que crean. **T018 debe llamar a `queue.shutdown()` y `monitor.shutdown()` en `closeEvent`, y hay que decidir allí si se avisa a la persona al cerrar con conversiones activas** (MarkItDown no se puede interrumpir: el cierre espera hasta 5 s a la conversión en curso).
- Componentes descargables (FR-016, T015): `core/components.py` (contratos), `app/components.py` (`ComponentManager`) y `adapters/ffmpeg_provider.py` (fuente fijada y descargador HTTPS). Instalan en `%LOCALAPPDATA%\FT Markdown\components\` (`local_data_dir()`/`components_dir()` en `app_paths.py`): son binarios regenerables y no se sincronizan; P12 protege ajustes e historial, que siguen en `%APPDATA%`. Decisiones que el SDD no cubría:
  - **Fuente:** BtbN/FFmpeg-Builds, serie n8.1, `win64-lgpl-shared`, tag `autobuild-2026-08-31-13-27` (último build de agosto: BtbN conserva los últimos 14 diarios y el último de cada mes durante dos años). SHA-256 `e9712ffb…db63`, calculado descargando el archivo y coincidente con `checksums.sha256` y con el digest que publica GitHub. `ffmpeg -version` no muestra `--enable-gpl` ni `--enable-nonfree`.
  - **Limitación del tag:** si BtbN retira ese tag, la descarga falla (error traducido) y hay que fijar otro tag y su hash en una versión nueva. **T027 debe verificar, antes de cada publicación, que la URL fijada en `FFMPEG` sigue activa** (`pytest -m network` lo comprueba de paso).
  - **Red (P11):** solo HTTPS hacia `github.com` y `*.githubusercontent.com` (la cadena real es un único salto a `release-assets.githubusercontent.com`); cualquier otra redirección se rechaza. Sin datos de la persona; solo `User-Agent: FT-Markdown`.
  - **Seguridad:** el SHA-256 se verifica antes de abrir el zip; se rechazan rutas con `..`, absolutas o con unidad; se extrae solo `ffmpeg.exe`, `ffprobe.exe`, las DLL y `LICENSE.txt` (~144 MB) y se mueve a su sitio de una vez. Descarga cancelable, parciales borrados y espacio libre comprobado (descarga + instalado + 50 MB).
  - **ffprobe:** `pydub` lo busca solo en el PATH y la prueba real lo detectó; el componente lo incluye y `_to_wav` añade su carpeta al PATH.
  - **Alcance:** `__main__` solo conecta la ruta del ejecutable (`ffmpeg_locator` del motor, consultado en cada conversión). El diálogo de confirmación y el texto (nombre, ~71 MB descarga, ~144 MB instalado, origen, LGPL) son de T021. Con `-m network` hay una prueba con descarga real; la transcripción real la verifica el usuario.
- Actualizaciones (FR-015, P11, T016): `core/updates.py` (versiones, errores, puertos), `adapters/network_policy.py` (política de red compartida con ffmpeg; ahora admite también `api.github.com`), `adapters/github_releases.py` y `app/updater.py` (`UpdateService`). Decisiones que el SDD no cubría:
  - **Versiones:** comparador SemVer 2.0.0 propio en `core` (el plan decía `packaging` en `app`, pero las reglas de capas lo impiden): numéricos como números, `+build` ignorado, prefijo `v` aceptado. Un tag ininterpretable nunca lanza: si es el único candidato, error traducido; si hay otros válidos, se ignora.
  - **Preliminares:** se consulta `GET /releases?per_page=10`; solo cuentan si la versión instalada es preliminar (T028 se prueba con betas marcadas como *pre-release*). Un tag con sufijo (`-beta.1`) cuenta como preliminar aunque no esté marcado; los borradores se ignoran.
  - **Registro de la consulta:** `last_update_check` se guarda cuando el servidor respondió (incluidos 403/429 y 5xx) y no si no se pudo conectar. Máximo un intento por arranque. `check(manual=True)` (T022, «Buscar ahora») ignora el interruptor, las 24 h y el límite por arranque. Una marca del futuro o ilegible no bloquea.
  - **Límites:** JSON ≤ 1 MiB, `.sha256` ≤ 4 KiB, instalador ≤ 300 MiB y exactamente el `size` que anuncia la API (se aborta al pasarse y se compara al terminar), más SHA-256. Límite de uso de GitHub (403/429) = error `RATE_LIMIT` con mensaje claro. Un `.sha256` con el nombre de otro archivo se rechaza.
  - **Descarga:** a `%LOCALAPPDATA%\FT Markdown\updates\` (`updates_dir()`); cada descarga borra primero lo anterior. `UpdateService.purge()` queda disponible para limpiar al arrancar.
  - **Nombres de assets:** constantes `INSTALLER_NAME_TEMPLATE` y `CHECKSUM_NAME_TEMPLATE`; una prueba las contrasta con `OutputBaseFilename` de `packaging/installer.iss`.
  - **Pruebas:** todas con doble de la fuente o del *opener*; `-m network` consulta la API real (una lista, o `RATE_LIMIT`).
  - **(a) Lanzar el instalador** no está en T016: irá en un adaptador con puerto en `core`, a cargo de **T023**, no en la interfaz. Debe esperar a que la cola esté vacía y llamar a `shutdown()` antes de cerrar.
  - **(b) Limitación del SHA-256:** prueba integridad, no autenticidad. Quien controle la release puede cambiar instalador y hash a la vez; hasta tener firma de código (plan §6) no hay garantía de origen.
  - **(c) T022** documenta `api.github.com` en el panel de privacidad y ofrece «Buscar actualizaciones».
  - **Decisión del autor (comprobación de actualizaciones):** activada por defecto, sin aviso en el primer arranque, con interruptor en ajustes. **T022 debe:** etiquetar el interruptor «Buscar actualizaciones al abrir la app, una vez al día, conectando a GitHub»; mostrar «Última comprobación» (`last_update_check`); ofrecer el botón «Buscar ahora» (`check(manual=True)`); y listar en el panel de privacidad `api.github.com`, `github.com` y `*.githubusercontent.com` (descarga) y las direcciones de la sonda de red (`1.1.1.1`, `8.8.8.8`). Interpretación de P11 registrada en la constitución v0.2.1.
  - **Plan §1 y §4 corregidos:** comparador propio y `GET /releases`.
- `requires-python` pasa a `>=3.12,<3.14`, coherente con el entorno de compilación.

## Fuera de esta lista (fase 2 del producto)

Credenciales y servicios externos (FR-013, HU-8): descripción de imágenes con LLM, OCR y Azure. Se abrirá una nueva especificación incremental cuando la v1 esté publicada.
