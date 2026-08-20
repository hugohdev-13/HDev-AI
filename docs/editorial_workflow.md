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
