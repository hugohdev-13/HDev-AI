# Provider OpenAI remoto

HDev AI usa el SDK oficial de Python y la Responses API para el provider
`openai`. El provider existe únicamente en backend: la clave nunca llega al
navegador, no se guarda en SQL Server y no se registra en logs.

## Configuración

Configura estas variables en Azure App Service o en el archivo `.env` local no
versionado:

```text
AI_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT_SECONDS=30
```

`OPENAI_API_KEY` es obligatoria. Si falta, el asistente editorial devuelve el
mensaje seguro “El proveedor de IA no está configurado.” No se muestran errores
técnicos al usuario.

## Comportamiento

`OpenAIProvider` llama `client.responses.create()` con:

- `instructions` editorial fuera de rutas;
- contenido limitado por `AI_MAX_ARTICLE_LENGTH`;
- Structured Outputs con JSON Schema estricto;
- `store=False`;
- timeout configurado al crear el cliente SDK.

La respuesta se valida como objeto JSON y se normaliza a
`EditorialSuggestionDTO`. El provider también implementa el contrato existente
de análisis, pero no persiste ni modifica artículos.

Las sugerencias son efímeras. El usuario debe aceptar cada campo en el editor y
guardar el formulario; `ArticleWorkflowService` conserva la autoridad sobre
los estados y la publicación.

## Observabilidad

Se registran provider, modelo, operación, resultado, latencia y usage cuando
la API lo devuelve (`input_tokens`, `output_tokens`, `total_tokens`). No se
persisten tokens ni costos todavía. Los logs no incluyen API keys, headers ni
el contenido completo del artículo.

## Prueba manual única

1. Instala dependencias: `pip install -r requirements.txt`.
2. Define las tres variables anteriores con una clave válida.
3. Inicia Flask e inicia sesión con un usuario que tenga `articles.edit`.
4. Edita un artículo existente y pulsa **Generar sugerencias** una sola vez.
5. Confirma que las sugerencias aparecen, acepta un campo y usa **Guardar
   cambios** explícitamente. Verifica que ningún estado se publicó de forma
   automática.
