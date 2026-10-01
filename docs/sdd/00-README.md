# FT Markdown — Desarrollo guiado por especificaciones (SDD)

## ¿Qué es SDD y por qué lo usamos aquí?

*Spec-Driven Development* (SDD) invierte el orden habitual de trabajo: en lugar de empezar escribiendo código y documentar después, primero se escribe **qué** debe hacer el sistema y **por qué**, se revisa y se aprueba, y solo entonces se decide **cómo** construirlo. El código pasa a ser una consecuencia verificable de la especificación, no al revés.

Para este proyecto aporta tres ventajas concretas. Primero, escalabilidad: cada función nueva (OCR, descripción de imágenes, Azure, una versión web o móvil) entra como un requisito más en la especificación y no como un parche improvisado. Segundo, trazabilidad: cada tarea de código apunta a un requisito (`FR-xxx`), así que siempre sabes por qué existe una línea de código. Tercero, control humano: entre cada fase hay un punto de revisión donde tú apruebas o corriges antes de seguir, lo que evita que el modelo tome decisiones de producto por ti.

## Fases y estado

| Fase | Documento | Pregunta que responde | Estado |
|---|---|---|---|
| 0. Constitución | `01-constitucion.md` | ¿Qué principios no negociables rigen el proyecto? | v0.2 — aprobada |
| 1. Especificación | `02-especificacion.md` | ¿Qué hace la app, para quién y por qué? | v0.2 — aprobada |
| 2. Plan técnico | `03-plan.md` + `../design/sistema-de-diseno.md` | ¿Con qué tecnología, arquitectura y diseño? | v0.2 — aprobado |
| 3. Desglose de tareas | `04-tareas.md` | ¿En qué pasos pequeños y comprobables se construye? | v0.1 — en revisión |
| 4. Implementación | `src/`, `tests/` | Código, pruebas y compilación del .exe | Pendiente |

Regla de avance: una fase no comienza hasta que la anterior está aprobada y sus preguntas abiertas (`[NECESITA ACLARACIÓN]`) están resueltas.

## Material de origen

- Código base: `markitdown-main 2/` (MarkItDown v0.1.8, Microsoft, licencia MIT). La carpeta `markitdown-main/` es una copia idéntica byte a byte y no se usará.
- `markitdown_gui.py` en la raíz está vacío (0 bytes); no se reutiliza.
