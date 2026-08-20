# Workflow editorial de artículos

## Estados

```text
draft -> review -> approved -> published
          ^          |            |
          |----------+            v
             draft <- published
```

Las transiciones permitidas son:

- `draft` → `review`
- `review` → `draft` o `approved`
- `approved` → `review` o `published`
- `published` → `draft`

Los artículos nuevos, incluidos los importados por RSS, comienzan siempre en
`draft`. No existen accesos directos a publicación desde el formulario.

## Responsabilidades

```text
POST /articles/<id>/status
        |
        v
ArticleWorkflowService.transition()
        |
        v
ArticleRepository.update() -> Article
```

La ruta mantiene autenticación y `articles.edit`, recibe solo el estado destino,
muestra mensajes flash y redirige al listado. `ArticleWorkflowService` valida
la transición contra `ArticleStatus`; por ello la interfaz no es el control de
seguridad principal.

## Publicación

La transición `approved` → `published` establece `published_at` si aún no
existe. La transición `published` → `draft` limpia `published_at`, para que el
artículo deje de considerarse publicado en consultas y vistas existentes.

## Compatibilidad

`Article.status` ya es una columna `String`, por lo que `review` y `approved`
no requieren migración. Los valores previos `draft` y `published` siguen siendo
compatibles. Las métricas del dashboard separan borradores, revisión,
aprobados y publicados.

## Editor de artículos

El editor administrativo permite modificar `title`, `slug`, `summary`,
`content`, `image_url`, `author`, `category_id` y `source_url`. El slug es
opcional: si se deja vacío al crear, se genera desde el título; si se indica,
se normaliza y se valida que no pertenezca a otro artículo.

`status`, `published_at` y las relaciones operativas no se aceptan desde el
formulario. Las transiciones continúan siendo exclusivas de
`ArticleWorkflowService`. Los artículos RSS muestran su fuente y URL original
como contexto, sin permitir modificar la fuente asociada. Un artículo publicado
puede editar sus campos de contenido con el comportamiento actual; no hay aún
versionado ni regreso automático a revisión.
