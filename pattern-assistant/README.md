# Pattern Authoring Assistant

Skill de Claude Code separada del skill de migración (`skill/`,
`specs/003-astro-migration-skill`) — se invoca **solo a mano**, nunca es
parte del loop de migración/sync.

**Fuente de verdad: [`SKILL.md`](./SKILL.md).** Este README es un resumen
de orientación. Spec, plan y tasks completos:
`specs/004-pattern-authoring-assistant/`.

## Para qué sirve

Cuando el skill de migración flaggea una página por no tener patrón
conocido, en vez de diseñar el componente Astro a mano desde cero, le
pasás a esta skill la URL o el slug de esa página. Ella releva su layout
(`get_rendered_structure`) y su contenido (`get_page_content`,
`get_media_original`), y redacta un primer borrador:

```text
astro-site/.pattern-drafts/<slug>/
├── component.astro   # borrador del componente de patrón, criterio libre
└── page.astro         # import + props + render — forma fija, ver contracts/draft-output.md
```

## Qué NUNCA hace

- No se dispara sola ni forma parte del flujo de `skill/SKILL.md`.
- No escribe en `src/components/` ni `src/pages/` — solo en
  `.pattern-drafts/` (gitignoreado, provisorio).
- No toca `astro-site/manifest.json` — registrar un patrón como
  aprobado es siempre una decisión humana, separada y explícita.
- No corre el chequeo de responsive ni el build — eso lo sigue haciendo
  `skill/SKILL.md`, una vez que el patrón está promovido y registrado.

## Después del borrador

Revisás/ajustás `component.astro`, lo movés vos mismo a
`src/components/`, adaptás `page.astro` a `src/pages/` (el `import` ya
apunta a la ruta correcta post-promoción — ver
`specs/004-pattern-authoring-assistant/contracts/draft-output.md`), y
agregás la entrada correspondiente a `astro-site/manifest.json`. De ahí
en más, `skill/SKILL.md` la trata como cualquier otra página migrada.
