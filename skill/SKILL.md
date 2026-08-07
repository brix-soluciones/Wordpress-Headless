---
name: "migrate-wp-to-astro"
description: "Migra o sincroniza una página de WordPress a un componente Astro existente en astro-site/: releva su layout, la clasifica contra astro-site/manifest.json, puebla contenido, y verifica responsive (5 viewports) y build reales antes de darla por terminada. Usa exclusivamente las tools del MCP (get_site_map, get_page_content, get_rendered_structure, get_media_original) — nunca llama a WordPress directamente."
argument-hint: "URL o slug de una página específica (opcional — si se omite, procesa todo el sitio vía get_site_map)"
compatibility: "Requiere el servidor MCP de specs/002-wp-mcp-tools configurado para la sesión, y astro-site/ con dependencias instaladas"
metadata:
  spec: "specs/003-astro-migration-skill/spec.md"
  plan: "specs/003-astro-migration-skill/plan.md"
user-invocable: true
disable-model-invocation: false
---

<!--
  Ensamblado incrementalmente por specs/003-astro-migration-skill/tasks.md
  (T001–T019) — historial completo ahí. Todas las secciones tienen
  contenido final; no quedan placeholders. Ver ese tasks.md antes de
  editar más: varias secciones se referencian entre sí a propósito
  (Verificar y Poblar componente son sub-procedimientos compartidos,
  invocados desde más de un lugar, no duplicados) — mantener esa
  estructura al modificar cualquier sección.
-->

## Preámbulo

**Nunca llamar directamente a WordPress.** Toda lectura de datos del
sitio de origen pasa exclusivamente por las cuatro tools del servidor MCP
(`specs/002-wp-mcp-tools`), ya configurado para esta sesión:

- `get_site_map()` — descubrimiento de todo el contenido publicado, con
  su `id`, `url`, `type`, y `modified` date.
- `get_page_content(id)` — contenido plano + custom fields de un post/page.
- `get_rendered_structure(url, selector?)` — layout renderizado (nunca
  `_elementor_data`).
- `get_media_original(slug)` — resolución original de una imagen.

No existe, ni debe existir, código en esta skill que haga un
fetch/curl/request HTTP directo a WordPress. Si alguna de estas tools
falla o el sitio no responde, detener el procesamiento de esa página
específica, reportar el error, y continuar con el resto del run — nunca
adivinar datos faltantes.

**Leer `astro-site/manifest.json`.** Antes de resolver el modo de
invocación (abajo):

1. Intentar leer `astro-site/manifest.json`.
2. Si el archivo no existe → tratarlo como `{ "pages": [] }` (ninguna
   página tiene patrón asignado todavía) — esto **no** es un error.
3. Si existe pero no es JSON válido, o `pages` no es un array →
   detenerse y reportar el manifest como inválido; no adivinar su
   contenido ni sobreescribirlo.
4. Si una entrada de `pages` no tiene `wp_slug`, `pattern`, `astro_file`,
   o el campo `last_synced_modified` → esa entrada se reporta como
   inválida y no cuenta como match válido para su `wp_slug`.

Esquema completo: `specs/003-astro-migration-skill/contracts/manifest-schema.md`.

**Modo de invocación, resolución de `id`, y ruteo.** Este skill acepta un
argumento opcional: la URL o el slug de una página específica. En
**ambos modos** (con o sin argumento), el primer paso siempre es llamar
`get_site_map()` — es la única fuente de `id` para cualquier página
(`get_page_content` lo requiere; ni el argumento del usuario ni
`get_rendered_structure` lo proveen), y permite bifurcar entre "página
nueva" y "página ya migrada" de la misma forma sin importar el modo.

1. Llamar `get_site_map()`.
2. Derivar el `wp_slug` de cada entrada devuelta: el último segmento no
   vacío del path de su `url` (p. ej. `https://origin-site.example/branding/`
   → `branding`). Es la misma clave que usa `astro-site/manifest.json`.
3. Seleccionar qué entradas procesar:
   - **Con argumento** (URL completa o slug) → filtrar a la única entrada
     cuyo `url` (si el argumento es una URL) o `wp_slug` derivado (si es
     un slug) matchea. **Si ninguna matchea** → detenerse y reportar que
     la página no aparece en `get_site_map()` — esto es un error de
     entrada, distinto de "página sin patrón" (esa página ni siquiera
     existe según WordPress).
   - **Sin argumento** → modo sitio completo: procesar todas las entradas.
4. Para cada entrada a procesar, buscar su `wp_slug` en
   `astro-site/manifest.json` (leído arriba):
   - **Entrada válida con `last_synced_modified` no nulo** → ya se pobló
     al menos una vez → sección *Sync de contenido*.
   - **Cualquier otro caso** (sin entrada, entrada inválida, o entrada
     válida pero `last_synced_modified` nulo — tiene patrón asignado pero
     todavía no se pobló nunca) → sección *Clasificar página nueva*, que
     resuelve ahí mismo si hay patrón asignado (población por primera
     vez) o no (flaggeo).

El `id` de la entrada resuelta en el paso 1 es el que usa
`get_page_content(id)` más adelante, en *Poblar componente* — no hace
falta (ni existe otra forma de) resolverlo de nuevo ahí.

## Clasificar página nueva

Aplica a toda página que el Preámbulo enrutó para acá — es decir, toda
página que **todavía no se pobló ni una vez** (`last_synced_modified`
nulo o inexistente): ya sea porque no tiene ninguna entrada de manifest
todavía, o porque tiene una entrada (patrón ya asignado por un humano)
pero nunca se ejecutó la población inicial.

**Decisión de match (MVP)**: el "patrón" de una página está determinado
**exclusivamente** por si existe o no una entrada válida de manifest para
su `wp_slug` — el skill nunca infiere ni adivina un patrón a partir del
layout relevado; esa decisión la toma siempre un humano, una única vez,
al agregar la entrada al manifest (Artículo III de la constitution). El
relevamiento (paso 1 abajo) no alimenta ningún clasificador automático —
existe para que la página quede evidenciada con datos frescos, se use
para poblar (si hay match) o como contexto para la decisión humana (si no
lo hay).

### Relevar y buscar en el manifest

1. Antes de tomar cualquier decisión, llamar `get_rendered_structure(url)`
   (FR-001) — nunca asumir el layout de memoria ni de una corrida
   anterior (Artículo II).
2. Buscar `wp_slug` entre las entradas de `pages` leídas en el Preámbulo.
   - **Si existe una entrada válida** (tiene `wp_slug`, `pattern`, y
     `astro_file` — Preámbulo punto 4) → esta página tiene patrón
     asignado (FR-002). Continuar a *Poblar componente* con esa entrada.
   - **Si no existe entrada, o la existente es inválida** → continuar a
     *Página sin patrón conocido*, abajo.

### Página sin patrón conocido

Se llega acá cuando, en *Relevar y buscar en el manifest*, no se
encontró una entrada de manifest válida para el `wp_slug` de esta
página.

1. **No crear, generar, ni forzar ningún componente ni archivo `.astro`**
   para esta página, bajo ninguna circunstancia (FR-003, FR-012). El
   skill nunca inventa un patrón ni un `pattern`/`astro_file` — esa
   asignación la hace siempre un humano, agregando la entrada
   correspondiente a `astro-site/manifest.json` (Artículo III).
2. Registrar la página como **flaggeada**, guardando (para el reporte,
   sección *Reportar → Páginas flaggeadas*):
   - `wp_slug` y `url`.
   - El relevamiento ya obtenido (el outline de `get_rendered_structure`,
     del paso 1 de *Relevar y buscar en el manifest*) — así un humano
     puede decidir el patrón sin tener que volver a pedirlo.
   - Un motivo breve: `"no manifest entry"` si no había ninguna entrada
     para este `wp_slug`, o `"invalid manifest entry"` si la había pero
     le faltaba algún campo requerido (Preámbulo punto 4).
3. **No detener el resto del run.** Si esta página es parte de un batch
   (modo sitio completo), seguir procesando el resto de las páginas con
   normalidad — una página flaggeada nunca bloquea a las demás (FR-014).
4. No reportar nada acá mismo — el reporte final de páginas flaggeadas se
   arma en *Reportar → Páginas flaggeadas*, no en este paso.

## Poblar componente

Aplica a toda página que llegó acá con una entrada de manifest válida —
desde *Clasificar página nueva* (rama de match, página nueva) o desde
*Sync de contenido* (página ya migrada que cambió — ver esa sección).

**Qué SÍ toca el skill**: únicamente el archivo de la página en
`astro_file` — específicamente, los datos/props que ese archivo le pasa
al componente de patrón que ya importa.

**Qué NUNCA toca**: el archivo del componente de patrón en sí (p. ej.
`src/components/PatternMVP.astro`), ni la estructura de
import/render que ya existe en `astro_file`. Ambos los escribió un
humano una única vez, al construir el patrón — el skill no genera ni
modifica markup de componente, solo aplica datos sobre lo que ya existe
(Artículo III/V).

**Ejemplo ilustrativo** (el nombre del patrón, sus props, y su forma
exacta son específicos de cada proyecto — esto solo concreta la
instrucción, no es un patrón fijo que todo proyecto deba tener):

Si `manifest.json` tiene
`{ "wp_slug": "branding", "pattern": "PatternMVP", "astro_file": "src/pages/branding.astro" }`,
y `branding.astro` ya contiene:

```astro
---
import PatternMVP from '../components/PatternMVP.astro';
const props = { title: '...', content: '...', heroImage: { src: '...', alt: '...' } };
---
<PatternMVP {...props} />
```

...entonces poblar esta página significa reescribir **únicamente** el
objeto `props` (nunca el `import`, nunca el `<PatternMVP {...props} />`):

1. `get_page_content(id)` → mapear `title` → `props.title`, `content` →
   `props.content`. Si la respuesta trae `custom_fields`, mapear cada uno
   al prop correspondiente que el patrón espere (definido por cómo lo
   construyó el humano — no algo que el skill infiera) (FR-004).
2. Para cada imagen que el patrón necesite (referenciada en el contenido
   o visible en el relevamiento de `get_rendered_structure`): derivar su
   `slug` a partir del nombre de archivo en el `src` — sacar la extensión
   y, si tiene, el sufijo de tamaño que WordPress agrega a las variantes
   generadas (`-{ancho}x{alto}`; p. ej.
   `team-photo-2026-1024x683.jpg` → slug `team-photo-2026`, **no**
   `team-photo-2026-1024x683`, que no es un slug de adjunto real). Con
   ese slug, resolver el archivo original con `get_media_original(slug)`
   y usar su `source_url` — nunca una variante recortada — para el prop
   de imagen correspondiente (p. ej. `props.heroImage.src`) (FR-004,
   hereda la garantía de `get_media_original` de nunca devolver un
   thumbnail).
3. Escribir `astro_file` con el `props` actualizado, dejando el resto del
   archivo byte-por-byte igual.

Si `get_page_content` o `get_media_original` fallan para esta página,
detenerse — **no** escribir un `astro_file` parcial — y reportar el
error (sección *Reportar*); no continuar a *Verificar* con datos
incompletos.

## Verificar (responsive + build)

Sub-procedimiento compartido — se invoca igual desde *Poblar componente*
(US1, página nueva) y desde *Sync de contenido* (US3, contenido
actualizado). FR-005 aplica a ambos casos: ninguna página cuenta como
terminada solo por haberse poblado o actualizado, tiene que pasar esto
primero.

1. Correr el build real del proyecto: `npm run build` dentro de
   `astro-site/`. Si falla, el resultado de este paso es
   `build_passed: false` — no seguir con el chequeo responsive para esta
   página, reportar el fallo del build tal cual (FR-007, FR-008).
2. Si el build fue exitoso, levantar `astro preview` (sirve el `dist/`
   recién generado — el chequeo responsive corre contra el build real,
   no contra el dev server, research.md #2) y esperar a que esté
   escuchando.
3. Invocar
   `node astro-site/scripts/check-responsive.mjs <preview-base-url> <path...>`
   (contrato: `contracts/check-responsive-cli.md`) con la(s) ruta(s) de
   la(s) página(s) que se están verificando en esta pasada — se pueden
   pasar varias rutas en una sola invocación.
   - **Importante (Windows)**: invocar este comando vía PowerShell, no
     vía Git Bash — Git Bash reescribe argumentos que empiezan con `/`
     (como `/branding/`) como rutas de archivo de Windows, lo que rompe
     la navegación del script (confirmado durante T005/T006's smoke test).
4. Parsear el JSON de salida (`{ "results": { "<path>": { "<width>": bool, ... } } }`).
   Para cada página: `responsive` es el objeto de 5 viewports tal cual lo
   devolvió el script; el resultado combinado de esa página es
   `complete = (los 5 viewports en true) AND build_passed`
   (`data-model.md`'s `VerificationResult`).
5. Si `complete` es `false`, identificar exactamente qué falló — qué
   viewport(s) no pasaron, o que el build falló — para incluirlo en el
   reporte (sección *Reportar*). Nunca reportar la página como terminada
   en ese caso (FR-006, FR-008).
6. Detener el proceso de `astro preview` al terminar de verificar todas
   las páginas de esta pasada.

## Reportar

### Páginas migradas o actualizadas

Para cada página poblada en *Poblar componente* — recién migrada (US1) o
actualizada por contenido (US3, *Sync de contenido*):

1. Invocar el sub-procedimiento *Verificar* (sección de arriba) para
   esta página — nunca reportar sin haber pasado por ahí primero.
2. Si `complete` es `true` → reportarla como **migrada** (o
   **actualizada**, según el caso), indicando: `wp_slug`, el
   `pattern`/`astro_file` usado, y confirmación de que los 5 viewports y
   el build pasaron (FR-006, FR-008 satisfechos).
3. Si `complete` es `false` → **no** reportarla como migrada/actualizada.
   Reportar exactamente qué falló — qué viewport(s) de los 5 no pasaron
   (si aplica) y/o el motivo del fallo de build — con detalle suficiente
   para que un humano actúe sin tener que re-correr nada (FR-006, FR-008).

### Páginas flaggeadas

Al final del run, listar todas las páginas registradas como flaggeadas
durante *Página sin patrón conocido* — **siempre por separado** de las
páginas migradas/actualizadas de la sección anterior, nunca mezcladas en
la misma lista (FR-015).

Para cada una: `wp_slug`, `url`, el motivo (`"no manifest entry"` /
`"invalid manifest entry"`), y un resumen breve del relevamiento
guardado (p. ej. las secciones/tags de nivel superior del outline) —
suficiente para que un humano decida el patrón sin tener que volver a
correr el skill.

Si el run no flaggeó ninguna página, esta sub-sección del reporte se
omite (o se indica explícitamente "ninguna página flaggeada") — no es un
error, es el caso feliz.

## Sync de contenido (páginas ya migradas)

Aplica a toda página que el Preámbulo enrutó para acá: tiene una entrada
de manifest válida con `last_synced_modified` **no nulo** — ya se pobló y
se sincronizó al menos una vez antes.

**Nunca se llama a `get_rendered_structure` en este flujo** (FR-009): el
layout ya se relevó, clasificó y verificó en la migración inicial (o en
un sync anterior); sync es exclusivamente contenido, nunca layout.

### Detectar cambios

1. Comparar el `modified` de la entrada de `get_site_map()` (ya resuelta
   en el Preámbulo, paso 1) contra el `last_synced_modified` de la
   entrada del manifest para este `wp_slug`.
   - **Son el mismo string** (comparación exacta — `last_synced_modified`
     siempre se guarda como copia literal del `modified` recibido, nunca
     reformateado; ver *Persistir el sync*, abajo, para por qué esto hace
     que la comparación sea segura sin parsear fechas) → esta página
     **no cambió** desde el último sync (FR-010). No hacer nada más con
     ella: no releer contenido, no reescribir `astro_file`, no invocar
     *Verificar*. No aparece en *Reportar → Páginas migradas o
     actualizadas* ni en *Páginas flaggeadas* — queda fuera de ambas
     listas porque no se tocó (consistente con "dejarla intacta", spec
     edge case). El resumen del run puede mencionar cuántas páginas se
     revisaron y no cambiaron, como una cifra, sin necesitar una lista
     nueva en *Reportar*.
   - **Son distintos** → el contenido cambió desde el último sync (la
     garantía de FR-010 es que `modified` siempre refleja la
     modificación real, así que cualquier diferencia es una señal
     confiable de cambio real). Continuar a *Actualizar contenido*, abajo.

### Actualizar contenido

2. Para cada página que cambió: invocar *Poblar componente* (sección de
   arriba) con la entrada de manifest de esta página — los mismos pasos
   que usa la migración nueva: `get_page_content(id)` → mapear
   `title`/`content`/`custom_fields` a los props de `astro_file`;
   `get_media_original(slug)` (con el mismo criterio de derivación de
   slug) para cada imagen; reescribir únicamente el objeto `props`,
   dejando el resto del archivo (incluida la estructura de
   import/render del componente de patrón) exactamente igual.
3. **Restricción adicional de sync**, más estricta que *Poblar
   componente* por sí sola: además de nunca tocar el archivo del
   componente de patrón, sync **nunca** reasigna `pattern` ni
   `astro_file` en la entrada del manifest — un sync actualiza contenido
   de una página que ya tiene patrón asignado, nunca le cambia el patrón
   (FR-011).
4. Invocar el sub-procedimiento *Verificar* (sección de arriba) para
   esta página. FR-005 aplica igual acá que en
   una migración nueva: un cambio de contenido no cuenta como
   "actualizado" solo por haberse escrito — tiene que volver a pasar
   responsive + build, aunque el layout no haya cambiado.

### Persistir el sync

5. Si `complete` (de *Verificar*) es `true` → escribir en
   `astro-site/manifest.json`, en la entrada de este `wp_slug`, el nuevo
   `last_synced_modified` = el `modified` que motivó este sync, copiado
   **tal cual, sin reformatear** (así la comparación por igualdad exacta
   del paso 1 sigue siendo válida la próxima vez). No tocar `pattern`,
   `astro_file`, ni `wp_slug` de esa entrada.
6. Si `complete` es `false` → **no** actualizar `last_synced_modified`.
   La próxima corrida va a volver a detectar esta página como cambiada
   (el `modified` real sigue sin coincidir con el `last_synced_modified`
   viejo) y va a reintentar el sync desde cero — un fallo de verificación
   nunca se pierde silenciosamente.
7. Reportar el resultado en *Reportar → Páginas migradas o actualizadas*
   (sección de arriba) — mismo formato que la migración nueva, marcando
   este caso explícitamente como **actualización** de contenido, no
   migración inicial.
