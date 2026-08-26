# Operación de IA

## Estado seguro del dashboard

El panel **Estado de IA** deriva su información de configuración local mediante
`AIHealthService`; no instancia providers, no realiza llamadas a OpenAI y no
consume tokens durante la carga del dashboard. Solo expone provider, modelo,
estado y disponibilidad de las capacidades editoriales. Nunca expone API keys,
headers, prompts, connection strings ni respuestas crudas.

Para `AI_PROVIDER=openai`, la ausencia de `OPENAI_API_KEY` se muestra como
`configuration_required` con un mensaje seguro. Los providers deterministas
actuales se consideran operativos sin una llamada remota. `AI_PROVIDER=disabled`
produce estado `disabled`.

## Métricas y observabilidad

`ArticleAnalysis` es el único resultado de IA persistido. El dashboard agrega
en una sola consulta sus estados `completed`, `failed` y
`pending`/`queued`/`processing`. Las sugerencias editoriales y revisiones
editoriales son efímeras, por lo que no se cuentan como métricas persistidas.

`OpenAIProvider` registra de forma segura operación, provider, modelo,
latencia y tokens cuando la Responses API los entrega. No se persisten tokens,
costos ni precios en esta etapa.

## Manejo de fallos

Los errores del provider se convierten en DTOs seguros sin modificar el
artículo ni su workflow. Un `RateLimitError`/HTTP 429 se registra por su tipo y
se trata como fallo seguro; no genera HTTP 500 ni cambia estados editoriales.
El estado `degraded` basado en el último 429 no se conserva porque requeriría
persistencia adicional; es una mejora futura.

`ArticleWorkflowService` conserva toda la autoridad de transición. La IA no
envía artículos a revisión, aprueba, publica, programa ni despublica. Una
edición humana posterior a aceptar una sugerencia puede activar las reglas de
workflow existentes.
