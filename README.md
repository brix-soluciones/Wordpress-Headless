# WP Headless Migration Toolkit

Skill + MCP + plugin de WordPress para migrar sitios WordPress/Elementor a
un frontend Astro headless, manteniendo WordPress como backend de contenido.

Ver `.specify/memory/constitution.md` para los principios de diseño acordados
antes de escribir código.

## Estructura

- `plugin/` — Plugin de WordPress (PHP). Normaliza la exposición REST del
  sitio: fuerza `show_in_rest` en CPTs y campos ACF, configura CORS, expone
  `/wp-json/migracion/v1/site-map` como punto único de descubrimiento.
- `mcp/` — Servidor MCP. Tools para que Claude (u otro agente) consulte el
  sitio WordPress: contenido plano vía REST nativo, HTML renderizado de
  páginas, media en resolución original, site-map del plugin.
- `skill/` — Skill (`SKILL.md`) con el procedimiento de migración:
  relevamiento, mapeo a patrones de componentes, construcción, verificación
  responsive, verificación de build. Consume las tools del MCP.
- `specs/` — Artefactos de spec-driven development (specs, plans, tasks) para
  cada uno de los tres componentes de arriba. La constitution vive en
  `.specify/memory/constitution.md`, no acá.

## Uso con spec-kit

La constitution ya está ratificada en `.specify/memory/constitution.md`.
Cada componente (plugin, mcp, skill) tiene su propio ciclo
`/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`,
todos atados a la misma constitution.
