# MCP — WordPress Migration Server

Servidor MCP que expone el sitio WordPress (contenido + estructura
renderizada) como tools consumibles por un agente.

## Tools planeadas

- `get_site_map()` — consulta `/wp-json/migracion/v1/site-map` del plugin;
  descubrimiento único de todo el contenido con fecha de modificación.
- `get_page_content(id)` — contenido plano vía REST nativo (`/wp/v2/pages`,
  `/wp/v2/posts`), incluye campos ACF si el plugin los expuso.
- `get_rendered_structure(url)` — HTML/DOM resuelto de una página pública
  (fetch o Playwright si hace falta JS). Fuente para el relevamiento inicial
  de layout — nunca `_elementor_data` (Artículo I y II).
- `get_media_original(slug)` — resolución original de una imagen vía
  `/wp/v2/media?slug=`, evita el recorte de thumbnail de Elementor.

`get_form_structure(form_id)` quedó fuera del alcance de
`specs/002-wp-mcp-tools` — candidato a una feature futura, no parte de
este plan.

## No hace

No genera código Astro directamente — le da datos a la skill, que es quien
decide cómo mapearlos a componentes.

## Stack

Python 3.11+, SDK oficial `mcp` (servidor stdio, sin framework web
adicional), `httpx` como cliente HTTP. Sin estado — cada tool hace fetch
al WordPress del proyecto (URL base configurable por variable de entorno,
`WP_MCP_BASE_URL`). Ver `specs/002-wp-mcp-tools/plan.md` para el detalle.
