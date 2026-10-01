# FT Markdown — guía para trabajar con una herramienta de código

App de escritorio para Windows que convierte documentos a Markdown usando MarkItDown (Microsoft, MIT), con identidad FungaTec. Se desarrolla con **SDD (Spec-Driven Development)**: primero se especifica, luego se implementa. El código nunca manda sobre los documentos; si hay conflicto, se corrige el documento primero y se deja constancia.

## Dónde está cada cosa

- `docs/sdd/01-constitucion.md`: principios P1–P12. **Gana sobre cualquier otro documento.**
- `docs/sdd/02-especificacion.md`: qué hace la app (HU, FR, NFR, criterios de éxito).
- `docs/sdd/03-plan.md`: cómo se construye (stack, capas, riesgos, trazabilidad).
- `docs/sdd/04-tareas.md`: lista de tareas T001–T029 con su criterio de terminado y el progreso.
- `docs/design/`: sistema de diseño y `tokens.json` (la interfaz solo consume estos tokens).

## Flujo para cada tarea

1. Lee la tarea en `04-tareas.md` y los requisitos que cita (FR/HU/P).
2. Escribe primero la prueba que define el comportamiento; confirma que falla.
3. Implementa lo mínimo para que pase. No añadas funciones fuera de la tarea.
4. Ejecuta `ruff format`, `ruff check` y `pytest`; todo debe quedar en verde.
5. Actualiza el progreso en `04-tareas.md`. Si algo contradice la especificación o el plan, corrige el documento y anótalo en su registro de cambios.
6. Un commit por tarea: `Txxx: resumen en español`. Al final, el trailer de coautoría que indique la herramienta.

## Protocolo por tarea (obligatorio)

Al recibir una tarea Txxx, antes de escribir código:

1. Lee la fila de la tarea en `04-tareas.md` y las secciones del plan y la especificación que cita.
2. Resume en un máximo de 5 líneas cómo la resolverás y **enumera cada decisión que el SDD no cubre** (servidores, bibliotecas, valores, licencias). Espera el visto bueno antes de implementar. Si ya tienes autorización expresa para seguir, anota igualmente esas decisiones en el commit y en `04-tareas.md`.
3. Contrasta cada decisión con la constitución (P1–P12), no solo con la tarea. Si una elección roza un principio (p. ej. conexiones de red sin motivo visible, P11), detente y plántealo.
4. Sigue el flujo de abajo. Al terminar, informa solo lo que verificaste: pega el resultado real de `pytest`, `ruff` y `git log --oneline -3`, sin resumir lo que no ejecutaste.

Higiene del repositorio:

- Añade archivos al commit **por nombre**, nunca con `git add .` ni `git add -A`. Deja fuera cambios ajenos a la tarea (p. ej. `tests/fixtures/markitdown/test_mskanji.csv`, que Windows modifica por fines de línea).
- El registro del hash en `04-tareas.md` va en un commit de documentación aparte.
- Nunca uses `--force`, `--no-verify` ni `git reset --hard` sin permiso expreso.
- Antes de cualquier `push`, comprueba que no entra nada de `build/`, `dist/`, instaladores, `.env` ni datos personales.
- Una sesión por tarea; el contexto vive en este archivo y en `docs/sdd/`, no en la conversación.

Revisión independiente (T029): quien revise no debe ser la sesión que escribió el código. Verifica contra los criterios de éxito §9 de la especificación, no contra la intención del autor.

## Reglas que no se rompen (las vigila `tests/unit/test_architecture.py`)

- `core` no importa nada del proyecto ni de terceros fuera de la biblioteca estándar. `adapters` importa `core`. `app` importa `core` y solo `PySide6.QtCore`. `ui` importa `app` y `core`. Solo `__main__.py` conecta las capas.
- `markitdown` se importa únicamente en `adapters/markitdown_engine.py`. Nunca se modifica su código (P1).
- Sin *plugins* de MarkItDown (`enable_plugins=False`); los convertidores se registran en el catálogo propio (P5).
- Local primero; lo que usa internet se identifica y se desactiva sin conexión (P3). Sin telemetría (P11).
- Datos del usuario solo en `%APPDATA%\FT Markdown`, nunca en la carpeta de instalación (P12). El historial guarda ruta, título, estado y fecha; **nunca el contenido** de los documentos (P4).
- Textos visibles en español con acentos y en un archivo de cadenas (P8). Colores y medidas solo desde tokens (P6).

## Comandos

```
powershell -ExecutionPolicy Bypass -File .\scripts\setup-dev.ps1   # entorno (Python 3.12 en .venv)
.\.venv\Scripts\python.exe -m pytest -q                            # pruebas
.\.venv\Scripts\python.exe -m ruff check src tests ; .\.venv\Scripts\python.exe -m ruff format src tests
.\.venv\Scripts\python.exe -m ft_markdown                          # abrir la app
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1       # .exe + instalador
```

## Cuidados

- Python **3.12** (no 3.14: Magika exige `onnxruntime<=1.20.1`, que no publica ruedas para 3.14).
- Los `.ps1` deben ser ASCII: Windows PowerShell 5.1 lee mal los acentos sin BOM.
- No hay datos personales en el repositorio. Los commits usan el correo *noreply* de GitHub; antes del primer `push` debe estar activa la opción "Block command line pushes that expose my email".
- `tests/fixtures/markitdown/` son archivos de MarkItDown (MIT); no se editan.
- Fase 2 (credenciales, LLM, OCR, Azure) está fuera de la v1: no se implementa.
