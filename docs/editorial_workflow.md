# Workflow editorial de artículos

## Estados

```text
draft -> review -> approved -> published
          ^          |            |
          |----------+            v
             draft <- published
```

Un artículo aprobado puede tener una programación opcional antes de publicarse:

```text
draft -> review -> approved -> scheduled (opcional) -> published
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

`scheduled_publish_at` no es un estado: conserva el artículo como `approved`
hasta que el comando de publicación automática realice la transición a
`published`. La fecha se persiste como UTC; el formulario interpreta el valor
local en `America/Mexico_City` y el dashboard lo muestra nuevamente en esa zona.
El comando externo es:

```powershell
python -m flask --app app.py publish-scheduled
```

Si el comando encuentra una programación vencida, publica mediante
`ArticleWorkflowService`. El dashboard solo advierte sobre estas publicaciones;
nunca cambia estados desde una petición web.

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

## Endurecimiento editorial

Para avanzar desde borrador a revisión, desde revisión a aprobado y desde
aprobado a publicado, el artículo debe contener título, slug, resumen y
contenido. Al publicar se comprueba además que el slug siga siendo único. La
imagen, categoría y URL de origen son opcionales.

Editar campos editoriales relevantes de un artículo `approved` (título, slug,
resumen, contenido, autor, categoría o imagen) lo devuelve automáticamente a
`review` para una nueva aprobación. Los artículos `published` conservan su
estado al editarse y el editor advierte que los cambios serán visibles. Al
despublicar (`published` → `draft`), `published_at` se conserva como dato
histórico; este campo sigue protegido contra entrada desde formularios.

## Vista previa editorial

`GET /articles/<id>/preview` es una ruta administrativa protegida por login y
`articles.view`. Permite visualizar artículos `draft`, `review`, `approved` y
`published` con el layout público, pero no realiza persistencia ni cambia
`status` o `published_at`. La vista se identifica con un banner y enlaces de
retorno al editor y listado. A diferencia de esta preview, las consultas
públicas continúan filtrando exclusivamente `status == "published"`.
