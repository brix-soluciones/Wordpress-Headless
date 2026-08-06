<!--
Sync Impact Report
==================
Version change: [TEMPLATE] → 1.0.0 (initial ratification)
Modified principles: n/a (first adoption, no prior version)
Added sections:
  - Core Principles I–VIII (all project-specific, supplied verbatim by project owner)
  - Governance
Removed sections:
  - [SECTION_2_NAME] / [SECTION_3_NAME] template placeholders — dropped intentionally.
    The 8 core principles fully cover the project's governance surface; no additional
    constraints/workflow content was supplied beyond them, so no empty scaffold sections
    were kept.
Deferred / TODO items: none — ratification date, amendment date, and version were all
  resolvable from this session (initial creation).
Templates requiring follow-up review (not modified by this command, per scope guard):
  - .specify/templates/plan-template.md — Constitution Check gates should reference
    Articles I, II, VI, VIII (Elementor exclusion, rendered-HTML relevamiento, responsive
    verification, build verification) where applicable.
  - .specify/templates/tasks-template.md — task categories for "manifest.json pattern
    definition" and "responsive check (5 viewports)" may need explicit task types.
-->

# WP Headless Migration Toolkit Constitution

Principios no negociables del proyecto. Todo spec/plan/tasks posterior debe
respetar esto; si algo entra en conflicto, se discute acá primero, no en el código.

## Core Principles

### I. No se lee `_elementor_data`

El árbol interno de widgets de Elementor no se traduce de forma confiable a
componentes de Astro (responsive settings propios, addons de terceros,
animaciones). Ninguna herramienta de este proyecto intenta parsear ese campo.

**Rationale**: Elementor serializa su propio modelo de layout, no HTML/CSS
portable; cualquier parser propio quedaría atado a la versión del plugin y a
los addons de terceros instalados en cada sitio origen, y se rompería en
silencio ante cambios. Es más barato y más confiable no depender de ese dato.

### II. Se lee el HTML renderizado, no el JSON interno

El relevamiento de layout se hace contra la página pública ya resuelta
(fetch o render con Playwright si hay JS pesado). Es más simple que el JSON
interno y funciona incluso contra sitios que no administramos.

**Rationale**: El HTML renderizado es la única representación estable y
universal del sitio origen — funciona sin importar el builder de página
usado, y no requiere acceso administrativo ni conocimiento de la estructura
interna de cada plugin.

### III. Patrón finito de componentes, por proyecto

No se intenta generar layout genérico para cualquier página. Cada proyecto
define un manifest propio (`manifest.json`) que mapea página → patrón de
componente conocido. Páginas que no encajan en ningún patrón existente se
flaggean para decisión humana, nunca se fuerzan.

**Rationale**: La generación genérica de layout es un problema abierto y no
confiable; un catálogo finito y explícito por proyecto es verificable,
revisable y falla de forma visible (flag) en vez de producir un componente
incorrecto silenciosamente.

### IV. Contenido plano vía REST nativo, sin plugin cuando se pueda

Posts, páginas y media se leen de `/wp-json/wp/v2/*`, que WordPress expone
de fábrica. El plugin propio (Artículo V) no reemplaza esto, lo complementa
donde WP no expone algo por defecto (CPTs sin REST, campos ACF).

**Rationale**: Minimiza la superficie de cambio requerida en el sitio
origen — la mayoría del contenido se migra sin instalar ni configurar nada
adicional.

### V. El plugin normaliza, no genera

El plugin de WordPress no crea datos nuevos. Su función es forzar
`show_in_rest` en CPTs/taxonomías/campos ACF que no lo tengan, configurar
CORS, y exponer un endpoint único de descubrimiento
(`/wp-json/migracion/v1/site-map`) con URL pública + tipo + fecha de
modificación de cada contenido, para sync incremental.

**Rationale**: Mantener el plugin como una capa de exposición/normalización,
en vez de un generador de datos, evita que el estado migrado diverja de la
fuente de verdad en WordPress y limita el alcance de lo que puede romperse.

### VI. Responsive verificable, no subjetivo

Ningún componente se da por terminado sin pasar un chequeo automatizado de
overflow horizontal (`scrollWidth` vs `clientWidth`) en al menos 5 viewports
(320, 375, 768, 1024, 1920px). Reglas de construcción: sin anchos/altos fijos
en contenedores de contenido, tipografía con `clamp()`, imágenes con
`max-width: 100%; height: auto`, grids con `minmax()` + `wrap`.

**Rationale**: "Se ve bien" no es un criterio verificable. Un chequeo
automatizado y reproducible en viewports fijos convierte "responsive" en un
gate binario que puede correr en CI, no en una revisión visual manual.

### VII. Formularios: WordPress solo como fuente, no como runtime

El envío de formularios no depende de que WordPress esté disponible en el
momento del submit. Estructura del form se lee vía REST; el envío real va a
backend propio → Resend. Protección antispam propia (mínimo honeypot).

**Rationale**: Desacoplar el runtime de envío de WordPress evita que la
disponibilidad o performance del sitio origen se convierta en un punto único
de falla para el sitio migrado.

### VIII. Verificación con build real

Ninguna tarea se marca terminada sin un `npm run build` limpio del sitio
Astro con la página/componente afectado presente en `dist/`.

**Rationale**: Un build exitoso y la presencia del artefacto en `dist/` es
la única confirmación objetiva de que un cambio es entregable; sin esto,
"terminado" es una afirmación no verificada.

## Governance

Esta constitución tiene precedencia sobre cualquier otra práctica, plantilla
o preferencia individual dentro de este proyecto. Todo spec, plan o tasks
generado por Spec Kit debe ser consistente con los ocho artículos anteriores;
donde haya conflicto, se resuelve enmendando esta constitución primero, no
ignorándola en el código.

**Enmiendas**: cualquier cambio a un artículo, o la adición/eliminación de
un artículo, requiere: (1) justificación explícita del motivo, (2) bump de
versión según semver (MAJOR = eliminación o redefinición incompatible de un
artículo; MINOR = artículo nuevo o expansión material de uno existente;
PATCH = aclaración o corrección de redacción sin cambio de regla), y (3)
actualización de `Última Enmienda` a la fecha del cambio.

**Revisión de cumplimiento**: `/speckit-plan` debe verificar el plan
propuesto contra estos artículos antes de generar tasks; cualquier
desviación debe quedar documentada y justificada en la sección de
Complexity Tracking del plan, no omitida silenciosamente.

**Versión**: 1.0.0 | **Ratificada**: 2026-08-03 | **Última Enmienda**: 2026-08-03
