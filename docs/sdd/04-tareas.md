# Fase 3 — Desglose de tareas · FT Markdown v1.0

**Versión:** 0.1 · **Fecha:** 2026-10-01 · **Estado:** en revisión · **Implementa:** Plan v0.2

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
| T018 | Ventana principal de dos columnas, zona de soltar y botón "Examinar" | FR-001 | Claude | Arrastrar y examinar funcionan, también con teclado |
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

## Fuera de esta lista (fase 2 del producto)

Credenciales y servicios externos (FR-013, HU-8): descripción de imágenes con LLM, OCR y Azure. Se abrirá una nueva especificación incremental cuando la v1 esté publicada.
