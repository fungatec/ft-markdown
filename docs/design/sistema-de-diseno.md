# Sistema de diseño — FT Markdown

**Versión:** 0.1 · **Fecha:** 2026-10-01 · **Estado:** en revisión (forma parte de la fase 2 del SDD) · **Fuente de verdad técnica:** `tokens.json`

## ¿Qué es este documento?

Un sistema de diseño es el conjunto de decisiones visuales tomadas una sola vez y reutilizadas en toda la app: colores, tipografía, espaciado, formas y comportamiento de cada componente. Se organiza en tres capas de *tokens* (valores con nombre). Los **primitivos** son los colores de marca en bruto. Los **semánticos** dicen para qué sirve cada color ("fondo", "texto secundario", "éxito"). Los **de componente** dicen qué usa cada pieza ("botón primario"). La interfaz solo consume tokens semánticos o de componente, nunca un HEX directo (Constitución P6); por eso cambiar de tema o ajustar la marca es editar un archivo.

Dirección visual, apoyada en la skill de UI/UX: estilo **Minimalismo / Suizo**, recomendado para herramientas profesionales y de productividad (jerarquía tipográfica clara, mucho espacio, geometría simple y alto contraste), con movimiento sutil (150–250 ms) y densidad estándar. La skill sugirió además una paleta verde azulado/naranja y la tipografía Inter; ambas se sustituyen por la identidad FungaTec, aunque Inter se conserva para el texto pequeño (ver §3).

## 1. Primitivos de color

| Token | HEX | Origen |
|---|---|---|
| `petroleo-900` | #053043 | Marca: azul petróleo |
| `petroleo-800` | #0A3E55 | Derivado: superficie elevada |
| `petroleo-700` | #0F4C68 | Derivado: superficie *hover* / seleccionada |
| `petroleo-500` | #2B6F8F | Derivado: divisores decorativos |
| `acero-400` | #578DA6 | Ilustraciones FungaTec: bordes de controles |
| `cielo-500` | #25A9E0 | Marca: azul cielo |
| `cielo-700` | #1B7FAA | Derivado: foco y enlaces en tema claro |
| `celeste-300` | #93CBE4 | Marca (obligatorio): acento |
| `verde-500` | #45AC4D | Marca: verde orgánico |
| `verde-700` | #2E7D34 | Derivado: éxito en tema claro |
| `niebla-50` | #F5F9FB | Derivado: fondo tema claro |
| `niebla-100` | #E8F1F5 | Derivado: texto principal tema oscuro |
| `niebla-300` | #A9C3D0 | Derivado: texto secundario tema oscuro |
| `pizarra-600` | #3D5A68 | Derivado: texto secundario tema claro |
| `coral-300` / `rojo-700` | #F2827F / #B3261E | Error (oscuro / claro) |
| `ambar-300` / `ambar-800` | #F2C14E / #8A5A00 | Advertencia (oscuro / claro) |

## 2. Tokens semánticos y contraste verificado

Relaciones de contraste WCAG 2.2 calculadas con la fórmula de luminancia relativa. Mínimos: 4.5:1 texto normal, 3:1 texto grande, íconos y bordes de controles.

| Rol semántico | Tema oscuro (predeterminado) | Contraste | Tema claro | Contraste |
|---|---|---|---|---|
| `bg/base` | #053043 | — | #F5F9FB | — |
| `bg/surface` | #0A3E55 | — | #FFFFFF | — |
| `bg/surface-hover` | #0F4C68 | — | #E8F1F5 | — |
| `text/primary` | #E8F1F5 | 12.1 | #053043 | 13.1 |
| `text/secondary` | #A9C3D0 | 7.6 | #3D5A68 | 6.9 |
| `text/accent` | #93CBE4 | 7.9 | #053043 | 13.1 |
| `action/primary` (fondo de botón) | #25A9E0 con texto #053043 | 5.2 | #25A9E0 con texto #053043 | 5.2 |
| `focus/ring` | #93CBE4 | 7.9 | #1B7FAA | 4.3 |
| `border/control` | #578DA6 | 3.8 | #3D5A68 | 6.9 |
| `border/divider` (decorativo) | #2B6F8F | n/a | #C9DCE6 | n/a |
| `status/success` | #45AC4D | 4.8 | #2E7D34 | 4.8 |
| `status/error` | #F2827F | 5.5 | #B3261E | 6.2 |
| `status/warning` | #F2C14E | 8.3 | #8A5A00 | 5.6 |

**Reglas que se desprenden del cálculo:**

- **Texto blanco sobre colores de marca: no.** Sobre #25A9E0 da 2.7:1 y sobre #45AC4D, 2.9:1. Los botones primarios y las insignias de éxito llevan siempre texto #053043.
- **Azul cielo y verde nunca son texto sobre fondo claro.** En ese contexto se usan sus derivados oscuros (`cielo-700`, `verde-700`).
- **El estado no depende solo del color.** Cada estado ("listo", "error", "en línea") lleva además ícono y texto, por accesibilidad para daltonismo.

## 3. Tipografía

| Uso | Familia | Tamaño / peso | Interlineado |
|---|---|---|---|
| Título de ventana / marca | Montserrat | 20 px / 600 | 1.3 |
| Encabezados de panel | Montserrat | 15 px / 600 | 1.3 |
| Texto de interfaz y botones | Inter | 14 px / 400–500 | 1.5 |
| Texto auxiliar (estados, rutas) | Inter | 13 px / 400 | 1.4 |
| Vista de código Markdown | JetBrains Mono | 13 px / 400 | 1.6 |

Montserrat aporta la identidad de marca, pero es ancha y pierde legibilidad en tamaños pequeños; por eso el texto funcional usa Inter, diseñada para pantallas. Las tres familias tienen licencia SIL OFL 1.1, así que pueden empaquetarse en una app distribuida gratuitamente si se incluye su licencia.

## 4. Espaciado, forma y movimiento

Escala de espaciado en múltiplos de 4: 4, 8, 12, 16, 24, 32, 48 px. Radios: 6 px en controles, 10 px en paneles y 16 px en la zona de soltar. Sin sombras en el tema oscuro (la elevación se expresa con `bg/surface`) y una sombra suave en el tema claro. Las transiciones de *hover* y foco duran entre 150 y 200 ms, y se desactivan si en Windows está desactivada la opción "Mostrar animaciones" (Accesibilidad → Efectos visuales).

## 5. Estructura de la pantalla principal

```
┌─────────────────────────────────────────────────────────────────┐
│ ◉ FT Markdown                     ● En línea   ⟳ Historial  ⚙  │  barra superior
├──────────────────────────┬──────────────────────────────────────┤
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐   │  documento.pdf          [Fuente|Vista]│
│     Suelta archivos       │  ────────────────────────────────── │
│     aquí o [Examinar]     │  # Título                           │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘   │  Texto convertido…                  │
│  [↗ Pegar URL o YouTube] │                                      │
│                           │                                      │
│  Cola (3)                 │                                      │
│  ✓ articulo.pdf    Listo  │                                      │
│  ◌ apuntes.docx  Convir…  │                                      │
│  ✕ scan.pdf  Sin texto ⓘ │                                      │
│                           │                                      │
│  Salida: …\Markdown [⋯]   │   [Copiar]  [Guardar .md]            │
│  [   Convertir todo   ]   │                                      │
└──────────────────────────┴──────────────────────────────────────┘
```

Una sola ventana con dos columnas: entrada y cola a la izquierda, resultado a la derecha. Los ajustes, el historial y "Acerca de" se abren como paneles laterales, sin cambiar de pantalla. Los avisos de actualización aparecen como una franja discreta bajo la barra superior.

## 6. Componentes y estados

| Componente | Estados obligatorios | Notas |
|---|---|---|
| Zona de soltar | reposo, arrastre activo (borde #93CBE4 discontinuo y fondo `surface-hover`), deshabilitada | Siempre acompañada del botón "Examinar": arrastrar no puede ser la única vía (WCAG 2.2, criterio 2.5.7) |
| Botón primario | reposo, *hover*, presionado, foco, deshabilitado, ocupado (con indicador) | Uno solo por vista: "Convertir todo" |
| Botón secundario | igual al primario | Borde `border/control`, fondo transparente |
| Fila de cola | pendiente, convirtiendo, listo, error, cancelado | Ícono + texto + color; el error muestra la causa al pasar el cursor o con el teclado |
| Indicador de conexión | en línea, sin conexión | Las acciones en línea se deshabilitan con una explicación, no se ocultan |
| Aviso de actualización | disponible, descargando (%), lista para instalar, error | Descartable; nunca modal |
| Vista previa | fuente (monoespaciada), renderizada | Seleccionable y copiable |

## 7. Iconografía

Íconos lineales SVG de **Lucide** (licencia ISC), trazo de 1.75 px y tamaños de 16 y 20 px, coloreados con `text/secondary` o `text/accent`. Nunca emojis como íconos. Todo botón que solo tiene ícono lleva un nombre accesible y un *tooltip*.

## 8. Lista de verificación antes de entregar cada pantalla

- [ ] Ningún color escrito directamente: todo sale de `tokens.json`.
- [ ] Contraste verificado en ambos temas.
- [ ] Recorrido completo con teclado (Tab, Enter, Esc) y foco siempre visible.
- [ ] Cada estado comunica con ícono y texto, no solo con color.
- [ ] La interfaz no se congela durante una conversión.
- [ ] Textos tomados del archivo de cadenas en español.
