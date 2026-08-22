# Publicación programada

Solo un artículo con estado `approved` y con título, slug, resumen y contenido
puede recibir una fecha `scheduled_publish_at`. La fecha se guarda como UTC sin
zona horaria. Programar o cancelar no cambia el estado ni `published_at`.

Si una edición editorial relevante devuelve un artículo aprobado a `review`, su
programación se elimina y necesita una nueva aprobación.

Un scheduler externo invoca el siguiente comando con la frecuencia operativa
definida fuera de Flask:

```powershell
python -m flask --app app.py publish-scheduled
```

El comando busca exclusivamente artículos aprobados cuya fecha programada ya
venció. Cada publicación usa `ArticleWorkflowService`; un fallo individual se
aísla, se incluye en el resumen y no detiene los artículos posteriores. La
salida informa `total`, `published` y `failed`; si existe algún fallo, el
comando termina con código distinto de cero para que el scheduler pueda alertar.
