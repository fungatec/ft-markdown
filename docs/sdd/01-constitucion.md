# Fase 0 — Constitución del proyecto

**Versión:** 0.2.1 · **Fecha:** 2026-10-01 · **Estado:** aprobada

## ¿Qué es este paso?

La constitución es el conjunto de principios que **no cambian de una función a otra**. Funciona como la "normativa interna" del proyecto: cuando más adelante haya que decidir entre dos caminos técnicos, la constitución decide. Se escribe antes que nada porque es lo que garantiza que la app siga siendo coherente cuando crezca. Modificarla es posible, pero exige justificarlo explícitamente y subir su versión.

## Principios

**P1. El motor de conversión es una dependencia, no código propio.** MarkItDown se usa tal como lo publica Microsoft, fijado a una versión concreta (v0.1.8 al inicio), sin modificar sus archivos. Toda interacción con él ocurre a través de una única capa adaptadora propia (`ConversionEngine`). *Razón:* así podemos actualizar MarkItDown sin romper la app y, si algún día cambia su API, solo se ajusta un archivo.

**P2. Arquitectura en capas con dependencias en una sola dirección.** Interfaz → servicios de aplicación → adaptador del motor. La interfaz nunca importa `markitdown` directamente, y los servicios nunca conocen detalles visuales. *Razón:* es la condición para reutilizar el mismo núcleo en otros frentes (línea de comandos, una versión web, integración con FungiDocs o FungiLab) sin reescribirlo.

**P3. Local primero, en línea de forma explícita.** Todo formato que pueda convertirse en el equipo se convierte sin red. Las funciones que requieren internet se identifican visualmente, fallan con un mensaje comprensible si no hay conexión y nunca bloquean las funciones locales.

**P4. Privacidad por defecto.** Ningún contenido de un documento sale del equipo sin que el usuario lo sepa: antes del primer uso de cada servicio externo se muestra un aviso. Las credenciales (fase 2) se guardan en el Administrador de credenciales de Windows, nunca en el código, en archivos de texto ni dentro del ejecutable.

**P5. Extensibilidad por registro explícito.** Los convertidores y servicios se registran en un catálogo propio de la app, no mediante descubrimiento automático de *plugins*. *Razón técnica:* MarkItDown descubre *plugins* con `importlib.metadata.entry_points`, mecanismo que no funciona de forma fiable dentro de un .exe empaquetado con PyInstaller. Registrar explícitamente evita fallos silenciosos en el ejecutable.

**P6. Un solo sistema de diseño.** Colores, tipografía, espaciado y radios se definen una vez como *tokens* y toda la interfaz los consume. Tema oscuro por defecto y tema claro disponible. Contraste mínimo WCAG 2.2 AA (4.5:1 para texto normal, 3:1 para texto grande y componentes).

**P7. Todo requisito es comprobable.** Cada requisito funcional tiene un criterio de aceptación y, siempre que sea posible, una prueba automatizada. Se reutilizan los archivos de prueba que ya trae MarkItDown (`tests/test_files/`).

**P8. Español primero, preparado para traducción.** Todos los textos de la interfaz viven en un archivo de cadenas, no dispersos en el código.

**P9. Respeto de licencias.** Se conservan el aviso MIT de MarkItDown y su `ThirdPartyNotices.md`, y se incluye una sección "Acerca de" con la atribución.

**P10. Versionado semántico.** `MAYOR.MENOR.PARCHE`. La v1.0.0 corresponde al alcance P1 de la especificación.

**P11. Distribución gratuita y transparente.** FT Markdown se distribuye sin costo, con licencia de código abierto, sin publicidad ni telemetría. Toda conexión a internet tiene un motivo visible para el usuario, y cada actualización publicada pasa las pruebas automatizadas antes de liberarse.

**P12. Las actualizaciones nunca ponen en riesgo los datos del usuario.** Ajustes e historial viven fuera de la carpeta de instalación (`%APPDATA%\FT Markdown`), de modo que instalar una versión nueva, o desinstalar, no los borra sin preguntar.

## Gobernanza

Un cambio a esta constitución se registra con fecha, motivo y versión nueva al final de este archivo. Si una especificación o plan contradice un principio, gana la constitución hasta que se enmiende.

## Registro de cambios

- 0.1 (2026-10-01): borrador inicial.
- 0.2 (2026-10-01): se agregan P11 y P12 tras decidir la distribución pública gratuita con instalador y actualizaciones.
- 0.2.1 (2026-10-01): aclaración de P11, sin cambiar ningún principio: «motivo visible» significa que la conexión está descrita en el panel de privacidad y se puede desactivar en ajustes. Motivo: decisión del autor sobre la comprobación de actualizaciones (activada por defecto, sin aviso en el primer arranque, con interruptor en ajustes).
