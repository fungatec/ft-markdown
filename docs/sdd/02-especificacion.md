# Fase 1 — Especificación funcional · FT Markdown

**Versión:** 0.2 · **Fecha:** 2026-10-01 · **Estado:** aprobada con cambios (preguntas Q-01 a Q-04 resueltas) · **Rige:** Constitución v0.2

## ¿Qué es este paso?

La especificación describe **qué** hace la aplicación y **por qué**, sin decir todavía con qué tecnología. Está escrita desde el punto de vista de quien la usa: historias de usuario priorizadas, requisitos numerados y criterios para saber si cada uno se cumple. Todo lo que aún no está decidido se marca como `[NECESITA ACLARACIÓN]`; ninguna de esas marcas puede quedar abierta cuando pasemos al plan técnico.

## 1. Problema y propósito

Convertir documentos académicos y de trabajo (PDF, Word, PowerPoint, Excel, páginas web, etc.) a Markdown es útil para estudiarlos, citarlos, alimentar modelos de lenguaje o archivarlos en bibliotecas como FungiDocs. MarkItDown resuelve la conversión, pero solo desde la línea de comandos o desde Python. Se necesita una aplicación de escritorio para Windows, con identidad FungaTec, que haga esa conversión en pocos clics y que esté diseñada para crecer en funciones sin rehacerse.

## 2. Usuarios

**Usuario principal:** el propio autor, estudiante e investigador que procesa artículos, presentaciones y apuntes. **Usuarios de la distribución pública:** estudiantes, investigadores y seguidores de FungaTec que descargan la app gratis, con conocimientos informáticos básicos y sin Python instalado. Esto obliga a que la instalación, las actualizaciones y los mensajes de error se entiendan sin ayuda técnica.

## 3. Inventario de capacidades de MarkItDown v0.1.8 (resultado del análisis)

Esta tabla proviene de revisar el código fuente en `markitdown-main 2/packages/markitdown/` y define qué puede ofrecer la app y en qué condiciones.

| Entrada | Convertidor | Requiere internet | Requiere credenciales | Observaciones |
|---|---|---|---|---|
| PDF | `PdfConverter` (pdfminer.six + pdfplumber) | No | No | PDF escaneados sin capa de texto devuelven poco o nada; el OCR es fase 2 |
| Word (.docx) | `DocxConverter` (mammoth) | No | No | Incluye ecuaciones (OMML) y comentarios |
| PowerPoint (.pptx) | `PptxConverter` | No | No | Incluye notas del orador |
| Excel (.xlsx / .xls) | `XlsxConverter` / `XlsConverter` | No | No | Cada hoja se vuelve una tabla |
| HTML, Wikipedia, RSS | Varios | No (archivo local) | No | |
| CSV, JSON, XML, TXT | `CsvConverter`, `PlainTextConverter` | No | No | Detección automática de codificación |
| Jupyter (.ipynb), EPUB, Outlook (.msg) | Varios | No | No | |
| ZIP | `ZipConverter` | No | No | Convierte recursivamente su contenido |
| Imágenes (.jpg, .png) | `ImageConverter` | No | No | Sin servicios extra solo extrae metadatos (y únicamente si `exiftool` está disponible); el texto o descripción requiere LLM (fase 2) |
| Página web por URL | `convert_url` | **Sí** | No | |
| Video de YouTube por URL | `YouTubeConverter` | **Sí** | No | Por defecto pide subtítulos en inglés; la app debe pedir español |
| Audio (.wav, .mp3, .m4a…) | `AudioConverter` | **Sí** | No | Usa el servicio gratuito *Google Web Speech*, sin garantía de servicio y poco apto para audios largos; mp3/m4a requieren ffmpeg; idioma por defecto `en-US`, la app debe pasar `es-MX` |
| Descripción de imágenes / diapositivas | `llm_client` | **Sí** | **Sí** (OpenAI u otro compatible) | Fase 2 |
| OCR de PDF escaneados e imágenes incrustadas | paquete `markitdown-ocr` | **Sí** | **Sí** (LLM) | Fase 2 |
| Azure Document Intelligence / Content Understanding | `DocumentIntelligenceConverter`, `cu_converter` | **Sí** | **Sí** (Azure) | Fase 2 |

Hallazgo técnico relevante para el plan: MarkItDown identifica el tipo de archivo con **Magika**, un modelo de aprendizaje automático local de Google. Funciona sin red, pero sus archivos de modelo deben empaquetarse explícitamente en el .exe.

## 4. Historias de usuario

**HU-1 · Convertir uno o varios archivos locales (P1 — MVP).** Como usuario, quiero arrastrar uno o varios archivos a la ventana y obtener su versión en Markdown, para no usar la terminal. *Aceptación:* al soltar un PDF, DOCX, PPTX o XLSX válido, la app muestra el Markdown resultante en menos de 10 s para archivos de hasta 20 páginas, sin conexión a internet.

**HU-2 · Revisar y guardar el resultado (P1).** Como usuario, quiero ver una vista previa del Markdown, copiarlo al portapapeles o guardarlo como `.md`, para usarlo de inmediato. *Aceptación:* el archivo guardado tiene el mismo nombre que el original con extensión `.md`, codificación UTF-8, y no sobrescribe un archivo existente sin preguntar.

**HU-3 · Conversión por lotes (P1).** Como usuario, quiero convertir una carpeta o un grupo de archivos y elegir una carpeta de salida, para procesar bibliografía completa. *Aceptación:* cada archivo muestra su estado (pendiente, convirtiendo, listo, error); un archivo fallido no detiene el resto; la interfaz no se congela durante el proceso.

**HU-4 · Errores comprensibles (P1).** Como usuario, quiero que, si un archivo no se puede convertir, la app me diga por qué en lenguaje claro y qué puedo hacer. *Aceptación:* los errores de formato no soportado, archivo dañado, falta de conexión y PDF sin texto tienen mensajes propios en español.

**HU-5 · Convertir desde una URL o un video de YouTube (P2).** Como usuario, quiero pegar un enlace y obtener el contenido en Markdown. *Aceptación:* si no hay conexión, la acción se desactiva con un aviso; las transcripciones de YouTube se piden primero en español y, si no existen, en inglés.

**HU-6 · Transcribir audio (P2).** Como usuario, quiero convertir una grabación corta a texto. *Aceptación:* se elige el idioma (español por defecto); se advierte del límite práctico de duración y de que el audio se envía a un servicio externo.

**HU-7 · Historial reciente (P2).** Como usuario, quiero ver las últimas conversiones y volver a abrir su resultado.

**HU-9 · Instalar la app (P1).** Como persona que descarga FT Markdown, quiero un instalador sencillo que no pida permisos de administrador y cree un acceso en el menú Inicio. *Aceptación:* la instalación termina en menos de 2 minutos en un equipo sin Python; existe desinstalador en "Aplicaciones instaladas" de Windows.

**HU-10 · Recibir actualizaciones (P1).** Como usuario, quiero que la app me avise cuando hay una versión nueva y la instale con un clic, sin perder mi configuración ni mi historial. *Aceptación:* la comprobación ocurre como máximo una vez al día, puede desactivarse en ajustes, nunca interrumpe una conversión en curso y verifica la integridad del instalador descargado antes de ejecutarlo.

**HU-8 · Servicios con credenciales (P3 — fase 2).** Como usuario, quiero configurar claves de OpenAI o Azure en una pantalla de ajustes para describir imágenes, aplicar OCR a PDF escaneados o usar Document Intelligence. *Aceptación:* las claves se almacenan en el Administrador de credenciales de Windows; se muestra un aviso de privacidad antes del primer uso.

## 5. Requisitos funcionales

- **FR-001** La app acepta archivos por arrastrar y soltar y por selector de archivos. *(HU-1)*
- **FR-002** Convierte sin red todos los formatos marcados como locales en la tabla §3. *(HU-1)*
- **FR-003** Muestra una vista previa del Markdown, con opción de ver el texto fuente y el renderizado. *(HU-2)*
- **FR-004** Permite copiar al portapapeles y guardar como `.md` en UTF-8. *(HU-2)*
- **FR-005** Procesa colas de archivos en segundo plano con estado individual y opción de cancelar. *(HU-3)*
- **FR-006** Permite elegir carpeta de salida y recuerda la última usada. *(HU-3)*
- **FR-007** Traduce las excepciones de MarkItDown (`UnsupportedFormatException`, `FileConversionException`, `MissingDependencyException`) y los errores de red a mensajes en español. *(HU-4)*
- **FR-008** Detecta la disponibilidad de internet y habilita o deshabilita las funciones en línea en consecuencia. *(HU-5, HU-6)*
- **FR-009** Convierte URL y videos de YouTube, priorizando subtítulos en español. *(HU-5)*
- **FR-010** Transcribe audio con idioma seleccionable, `es-MX` por defecto. *(HU-6)*
- **FR-011** Guarda un historial local de las últimas 50 conversiones. *(HU-7)*
- **FR-012** Muestra una sección "Acerca de" con versión de la app, versión de MarkItDown y avisos de licencia. *(P9)*
- **FR-014** Se distribuye mediante un instalador para Windows, por usuario (sin permisos de administrador), con desinstalador. *(HU-9)*
- **FR-015** Comprueba si hay versiones nuevas en el canal de publicación, muestra un aviso no intrusivo y, con confirmación, descarga, verifica (SHA-256) y ejecuta el instalador nuevo conservando ajustes e historial. *(HU-10)*
- **FR-016** Los componentes pesados y opcionales (ffmpeg para audio MP3/M4A) se descargan bajo demanda la primera vez que se necesitan, con confirmación del usuario. *(HU-6, NFR-006)*
- **FR-013** *(fase 2)* Pantalla de ajustes con gestión segura de credenciales y aviso de privacidad. *(HU-8)*

## 6. Requisitos no funcionales

- **NFR-001 Plataforma:** Windows 10 y 11, 64 bits; ejecutable que no exige instalar Python.
- **NFR-002 Rendimiento:** la ventana abre en menos de 5 s; la interfaz responde durante conversiones largas.
- **NFR-003 Accesibilidad:** contraste WCAG 2.2 AA; navegable con teclado; tamaño de texto legible (mínimo 13 px en interfaz).
- **NFR-004 Privacidad:** cero llamadas de red al convertir formatos locales; sin telemetría ni analítica de uso. Las únicas conexiones son las que el usuario activa (URL, YouTube, audio, descargas de componentes) y la comprobación de actualizaciones, que puede desactivarse.
- **NFR-005 Mantenibilidad:** actualizar MarkItDown a una nueva versión no requiere modificar la interfaz.
- **NFR-006 Tamaño:** instalador por debajo de 150 MB y aplicación instalada por debajo de 350 MB (estimación a confirmar en la primera compilación; pandas, Qt y Magika/onnxruntime son los componentes más pesados).
- **NFR-007 Distribución:** gratuita, con licencia de código abierto y avisos de todas las licencias de terceros incluidos en la app.

## 7. Identidad visual (insumo para el sistema de diseño)

Se usa la paleta oficial de FungaTec, con #93CBE4 como celeste obligatorio en lugar de #A7F0F3 (decisión del autor, 2026-10-01). Tipografía de marca: Montserrat. El sistema de diseño completo, con tokens y contrastes verificados, está en `docs/design/sistema-de-diseno.md`.

| Color de marca | HEX | Papel principal |
|---|---|---|
| Azul petróleo | #053043 | Fondo del tema oscuro; texto en el tema claro |
| Azul cielo | #25A9E0 | Acción principal (botón primario), enlaces sobre fondo oscuro |
| Celeste | #93CBE4 | Acento obligatorio: títulos destacados, foco, selección, zona de soltar |
| Verde orgánico | #45AC4D | Estados de éxito ("listo") |

## 8. Fuera de alcance de la v1

Edición del Markdown dentro de la app (más allá de la vista previa), conversión de Markdown a otros formatos, sincronización en la nube, versiones para macOS o móvil, y las funciones con credenciales (fase 2).

## 9. Criterios de éxito de la v1

Los 25 archivos de prueba incluidos en MarkItDown que corresponden a formatos locales (PDF, DOCX, PPTX, XLS/XLSX, HTML, CSV, JSON, XML, IPYNB, EPUB, MSG y ZIP) producen Markdown desde la interfaz, y los PDF escaneados muestran el aviso de "PDF sin texto" en lugar de un resultado vacío; ningún formato local produce tráfico de red; un archivo dañado dentro de un lote no interrumpe los demás; el .exe se ejecuta en un Windows sin Python instalado.

## 10. Preguntas abiertas y decisiones

Resueltas el 2026-10-01:

- **Q-01 · Nombre:** FT Markdown.
- **Q-02 · Paleta:** paleta oficial de FungaTec, sustituyendo #A7F0F3 por #93CBE4.
- **Q-03 · Escalabilidad:** distribución gratuita a otras personas, con instalador y actualizaciones.
- **Q-04 · Compilación:** local, con el Python instalado en Windows del autor.

- **Q-05 · Python:** el equipo tiene 3.14.8; se instalará 3.12 en paralelo para compilar (3.14 es incompatible con Magika/onnxruntime en Windows).
- **Q-06 · GitHub:** las versiones se publican en la cuenta personal `fungatec` de GitHub (repositorio público `ft-markdown`). Se creará antes de la tarea T016; la prueba de concepto no lo necesita.
- **Q-07 · Licencia:** pendiente de confirmar (recomendada: MIT). No bloquea el inicio de las tareas.
