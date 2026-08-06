# Plugin — Migration Toolkit for WordPress

WordPress plugin (PHP) que normaliza cualquier instalación para que hable el
mismo idioma con el MCP, sin importar cómo esté configurada de origen.

## Alcance (ver Artículo V de la constitution)

- [x] Forzar `show_in_rest` en todos los CPTs registrados que no lo tengan
      (filtro `register_post_type_args`).
- [x] Forzar `show_in_rest` en todos los grupos de campos ACF
      (`acf/rest_api/field_settings`), sin depender de "ACF to REST API"
      como plugin externo.
- [x] Headers CORS correctos para que Astro (otro dominio) pueda hacer
      fetch en build time.
- [x] Endpoint propio `/wp-json/migracion/v1/site-map`: devuelve todos los
      posts/páginas/CPTs con URL pública, tipo, y fecha de modificación
      (para sync incremental).
- [ ] Panel de admin "estado de migración": qué está expuesto y qué no
      (CF7 activo, CPTs sin REST, ACF sin exponer). **Fuera de alcance**
      de `specs/001-wp-rest-normalizer/` — no está en los functional
      requirements de esa spec (ver `research.md` de esa feature).
      Candidato a spec propia si se necesita.

## No hace

No lee ni expone `_elementor_data` (Artículo I). No genera contenido nuevo,
solo expone lo que ya existe.

## Estructura

```
plugin/
  migration-toolkit.php          # bootstrap, header del plugin, wiring
  readme.txt                     # readme estilo WordPress.org
  includes/
    functions.php                # helper compartido (post types públicos)
    class-rest-normalizer.php    # show_in_rest forzado (CPTs + ACF)
    class-sitemap-endpoint.php   # /wp-json/migracion/v1/site-map
    class-cors.php                # CORS configurable
```

Ver `specs/001-wp-rest-normalizer/` (spec, plan, tasks) para el detalle de
esta implementación.
