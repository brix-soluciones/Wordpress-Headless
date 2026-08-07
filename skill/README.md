# Skill — WordPress → Astro Headless Migration

Procedimiento que sigue el agente para migrar/sincronizar una página de
WordPress a un componente Astro, usando las tools del MCP
(`specs/002-wp-mcp-tools`).

**Fuente de verdad: [`SKILL.md`](./SKILL.md).** Este README es un resumen
de orientación; el procedimiento completo, con todas las reglas exactas
(comparaciones, formatos de error, casos límite), vive ahí. Spec, plan y
tasks completos: `specs/003-astro-migration-skill/`.

## Flujo

1. **Preámbulo**: llamar `get_site_map()` (siempre primero, en ambos
   modos de invocación — es la única fuente del `id` numérico que
   requiere `get_page_content`), leer `astro-site/manifest.json`, y
   rutear cada página según tenga o no una entrada con
   `last_synced_modified` ya seteado.
2. **Página nueva** (sin entrada, o entrada sin sincronizar todavía):
   - **Relevar** con `get_rendered_structure(url)` — nunca asumir layout
     de memoria (Artículo II).
   - **Clasificar**: ¿tiene entrada de manifest válida?
     - Sí → **Poblar** el componente existente con `get_page_content`
       (texto/custom fields) y `get_media_original` (imágenes).
     - No → **flaggear**, nunca forzar ni generar un componente
       (Artículo III); seguir con el resto del batch.
3. **Página ya migrada** (entrada con `last_synced_modified` seteado):
   comparar `modified` contra `last_synced_modified`; si no cambió,
   dejarla intacta; si cambió, **Poblar** de nuevo (sin re-relevar
   layout) y actualizar `last_synced_modified`.
4. **Verificar** (toda página poblada, nueva o actualizada): build real
   (`npm run build`) + `astro preview` + chequeo de overflow en los 5
   viewports (`astro-site/scripts/check-responsive.mjs`) — Artículos VI
   y VIII. No se reporta como terminada si falla cualquiera de las dos.
5. **Reportar**: páginas migradas/actualizadas, páginas flaggeadas (por
   separado), y cualquier error — nunca mezclados.

## manifest.json (por proyecto, no genérico)

Vive en `astro-site/manifest.json` — **no** en esta carpeta (`skill/`).
Esquema completo: `specs/003-astro-migration-skill/contracts/manifest-schema.md`.

```json
{
  "pages": [
    {
      "wp_slug": "branding",
      "pattern": "portfolio",
      "astro_file": "src/pages/branding.astro",
      "last_synced_modified": "2026-08-05T14:00:00+00:00"
    }
  ]
}
```

`last_synced_modified` es `null` hasta el primer sync exitoso de esa
página. Ver Artículo III de la constitution — este archivo es lo único
que cambia entre proyectos, la skill en sí es genérica.
