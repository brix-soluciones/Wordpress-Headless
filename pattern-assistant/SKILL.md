---
name: "draft-astro-pattern"
description: "Ayuda a redactar un primer borrador de un componente de patrón Astro (y la página que lo usa) a partir del layout y contenido reales de una página de WordPress específica — normalmente una que el skill de migración (specs/003-astro-migration-skill) flaggeó por no tener patrón conocido. Nunca se dispara sola, nunca es parte del loop de migración/sync, nunca registra el patrón como aprobado — eso lo decide siempre un humano."
argument-hint: "URL o slug de la página específica a usar como referencia (requerido)"
compatibility: "Requiere el servidor MCP de specs/002-wp-mcp-tools configurado para la sesión, y astro-site/ presente"
metadata:
  spec: "specs/004-pattern-authoring-assistant/spec.md"
  plan: "specs/004-pattern-authoring-assistant/plan.md"
user-invocable: true
disable-model-invocation: false
---

<!--
  Ensamblado por specs/004-pattern-authoring-assistant/tasks.md (T001–T008).
  Skill separada de skill/SKILL.md (specs/003) a propósito — nunca la
  invoca ni es invocada por ella. Ver tasks.md antes de editar más.
-->

## Preámbulo

Este skill requiere un argumento: la URL o el slug de una página
específica del sitio de origen — normalmente la que acabás de ver
flaggeada por el skill de migración (`skill/SKILL.md`,
`specs/003-astro-migration-skill`). No tiene modo sitio-completo:
procesa siempre una sola página por invocación.

1. Llamar `get_site_map()`.
2. Derivar el `wp_slug` de cada entrada devuelta: el último segmento no
   vacío del path de su `url` (misma regla que usa el Preámbulo de
   `skill/SKILL.md`).
3. Matchear el argumento contra las entradas: si es una URL completa,
   comparar contra `url`; si es un slug, comparar contra el `wp_slug`
   derivado.
   - **Si ninguna entrada matchea** → detenerse y reportar que la página
     no aparece en `get_site_map()` — no intentar adivinar ni continuar
     con datos parciales (FR-008).
   - **Si matchea** → queda resuelto el `id` y el `url` de esa entrada;
     ambos se usan en el resto del flujo, no hace falta resolverlos de
     nuevo.
4. Chequear si `astro-site/.pattern-drafts/<slug>/` ya existe (usando el
   `wp_slug` derivado en el paso 2 como `<slug>`).
   - **Si existe** → detenerse y avisarle al humano — nunca sobreescribir
     un borrador existente sin que decida qué hacer (FR-009). No
     continuar al resto del flujo.
   - **Si no existe** → continuar a *Recopilar datos*.

## Recopilar datos

1. Llamar `get_rendered_structure(url)` con la `url` resuelta en el
   Preámbulo — antes de escribir cualquier archivo (FR-001).
2. Llamar `get_page_content(id)` con el `id` resuelto en el Preámbulo.
3. Para cada imagen que el outline o el contenido referencien y que el
   borrador vaya a necesitar: derivar su slug igual que "Poblar
   componente" en `skill/SKILL.md` — sacar la extensión y, si tiene, el
   sufijo de tamaño `-{ancho}x{alto}` que WordPress agrega a las
   variantes generadas — y resolverla con `get_media_original(slug)`,
   usando siempre su `source_url` (nunca una variante recortada) (FR-010).
4. Si `get_rendered_structure`, `get_page_content`, o `get_media_original`
   fallan en cualquier momento → detenerse y reportar el error con
   claridad — no redactar ningún archivo con datos parciales o
   adivinados (FR-008). No continuar a las secciones de redacción.

## Redactar el componente de patrón

No hay un algoritmo fijo para traducir el outline relevado a markup de
Astro — a propósito. La generación de layout genérico es exactamente lo
que la constitution (Artículo III) mantiene como decisión humana, no
automatizable; este paso es asistencia para esa decisión, no un
reemplazo. Usar criterio al redactar, con el outline y el contenido
recopilado como referencia real, no como una plantilla a seguir al pie
de la letra.

1. Con el outline de `get_rendered_structure` (*Recopilar datos*, paso 1)
   como referencia, redactar un componente Astro que refleje la
   estructura real de la página — secciones y jerarquía — usando el
   texto/imágenes ya recopilados como contenido de ejemplo (contenido
   real, no placeholders genéricos, para que el humano vea cómo se ve
   con datos reales).
2. Elegir un nombre de componente descriptivo a partir del `title` de
   `get_page_content` o del `wp_slug` — el humano lo puede renombrar
   libremente después, esto es solo para que el borrador tenga un
   nombre razonable desde el vamos.
3. Escribir el archivo en `astro-site/.pattern-drafts/<slug>/component.astro`
   (`contracts/draft-output.md`) — **nunca** en `src/components/` ni en
   ninguna otra ubicación que el skill de migración trate como patrón ya
   aprobado (FR-004).
4. Este archivo es un borrador para revisión humana, no un patrón
   registrado — nada en este paso lo agrega a `astro-site/manifest.json`
   ni lo hace "conocido" para el skill de migración (FR-002, FR-004,
   FR-006). Dejar explícito en la respuesta al humano: qué archivo se
   creó, y que falta su revisión y la decisión de promoverlo.

## Redactar el archivo de página

A diferencia de *Redactar el componente de patrón*, esta sección **no**
tiene margen de criterio libre — la forma exacta importa, porque es el
contrato real con `skill/SKILL.md` (`specs/003-astro-migration-skill`,
`contracts/draft-output.md`).

1. Usando el componente recién redactado, escribir
   `astro-site/.pattern-drafts/<slug>/page.astro` con exactamente esta
   forma:
   - Un único `import` del componente, con la ruta relativa que va a
     tener **después de promoverse** — `../components/NombreComponente.astro`,
     como si `page.astro` ya estuviera en `src/pages/` y `component.astro`
     en `src/components/` — **no** la ruta relativa dentro de
     `.pattern-drafts/<slug>/` (donde ambos archivos son hermanos y
     `./component.astro` sería la ruta real, pero rota apenas se
     promueva). El staging es temporal; la ruta escrita tiene que ser
     correcta en el destino final, no en el lugar donde vive mientras es
     un borrador.
   - Un único `const props = { ... }`, armado con el `title`/`content`/
     `custom_fields` de `get_page_content` y las `source_url` de las
     imágenes resueltas en *Recopilar datos* — sin estructura adicional.
   - Una única línea de render: `<Componente {...props} />`.
2. No agregar nada más al archivo — ni imports adicionales, ni lógica, ni
   otro markup. Motivo puntual: `skill/SKILL.md` nunca toca nada de
   `astro_file` salvo el objeto `props` — la primera vez que ese skill
   procese esta página (una vez que un humano la agregue al manifest),
   tiene que encontrar exactamente esta forma para poder reescribir el
   `props` correctamente, sin reestructurar nada a mano antes.
3. Reportar al humano ambos archivos juntos (`component.astro` y
   `page.astro`) como resultado de esta corrida — recordando que
   promoverlos a `src/` y agregar la entrada a
   `astro-site/manifest.json` son acciones separadas y explícitas que
   este skill nunca hace (FR-004, FR-006).
