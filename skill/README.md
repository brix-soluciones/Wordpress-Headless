# Skill — WordPress → Astro Headless Migration

Procedimiento que sigue el agente para migrar/sincronizar una página de
WordPress a un componente Astro, usando las tools del MCP.

## Flujo

1. **Relevar** la página en vivo con `get_rendered_structure(url)` — nunca
   asumir contenido de memoria (Artículo II).
2. **Clasificar** contra `manifest.json` del proyecto: ¿coincide con un
   patrón de componente existente?
   - Sí → ir a 3.
   - No → flaggear como caso nuevo, pedir decisión humana. No forzar
     (Artículo III).
3. **Poblar** el componente existente con el contenido relevado
   (`get_page_content` para texto/ACF, `get_media_original` para imágenes).
4. **Verificar responsive**: correr el chequeo de overflow en los 5
   viewports (Artículo VI). No sigue si falla.
5. **Verificar build**: `npm run build` limpio con la página en `dist/`
   (Artículo VIII).
6. **Reportar**: qué cambió, si pasó ambas verificaciones, y si algo quedó
   flaggeado sin resolver.

## Para actualizaciones posteriores (contenido ya migrado)

Si la página ya tiene componente Astro asignado en el manifest, saltar el
paso 1-2 (relevamiento de layout) y usar `get_site_map()` +
`get_page_content()` para sync incremental de solo lo que cambió
(comparar `modified date`).

## manifest.json (por proyecto, no genérico)

```json
{
  "pages": [
    { "wp_slug": "branding", "pattern": "portfolio", "astro_file": "src/pages/branding.astro" }
  ]
}
```

Ver Artículo III de la constitution — este archivo es lo único que cambia
entre proyectos, la skill en sí es genérica.
