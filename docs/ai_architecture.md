# Arquitectura actual de IA

Este documento describe exclusivamente la implementación existente de HDev AI
al cierre de Sprint 8 Entrega 1. No describe generación editorial ni una
integración remota de proveedores que todavía no exista.

## Componentes

- `ai/services/ai_service.py`: orquestador sin persistencia. Valida el artículo
  mediante el provider, ejecuta su análisis, normaliza el DTO y transforma
  errores en un resultado `failed` sin incluir la excepción original.
- `ai/factory/provider_factory.py`: selecciona un provider por `AI_PROVIDER`.
- `ai/providers/base_provider.py`: contrato común y validación de título más
  contenido o resumen; limita el texto a `AI_MAX_ARTICLE_LENGTH`.
- `ai/dto/article_analysis.py`: `ArticleAnalysisDTO`, contrato normalizado del
  resultado de análisis.
- `services/article_analysis_service.py`: coordina lectura de `Article`, uso de
  `AIService` y persistencia transaccional de una sola fila de análisis.
- `services/automatic_analysis_service.py`: decide si el análisis se dispara
  automáticamente después de crear o editar un artículo.
- `repositories/article_analysis_repository.py`: encapsula commits y rollback
  para `ArticleAnalysis`.
- `models/article_analysis.py`: persistencia uno a uno mediante
  `article_analyses.article_id`, que es único.

## Providers

`ProviderFactory` soporta `openai`, `gemini`, `azure`/`azure_openai` y
`ollama`. `gemini`, `azure` y `ollama` continúan siendo implementaciones
deterministas locales. `openai` usa el SDK oficial de Python y la Responses API
cuando `OPENAI_API_KEY` está configurada. Si falta configuración, devuelve un
resultado seguro fallido y no realiza ninguna llamada de red.

OpenAI usa Structured Outputs con JSON Schema estricto para sugerencias
editoriales y timeout configurable. La configuración y prueba manual están
documentadas en [openai_provider.md](openai_provider.md).

## Configuración

`core/ai_config.py` centraliza valores de entorno sin almacenar secretos:

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| `AI_PROVIDER` | `openai` | Provider seleccionado por la factory. |
| `OPENAI_MODEL` | `mock-openai` | Metadato del provider OpenAI de prueba. |
| `GEMINI_MODEL` | `mock-gemini` | Metadato del provider Gemini de prueba. |
| `AZURE_OPENAI_MODEL` | `mock-azure` | Metadato del provider Azure de prueba. |
| `OLLAMA_MODEL` | `mock-ollama` | Metadato del provider Ollama de prueba. |
| `AI_MAX_ARTICLE_LENGTH` | `12000` | Límite de texto enviado al provider. |
| `AI_SUMMARY_MAX_WORDS` | `200` | Límite de resumen determinista. |
| `AI_AUTO_ANALYZE_ON_CREATE` | `true` | Habilita análisis tras crear. |
| `AI_AUTO_ANALYZE_ON_UPDATE` | `false` | Habilita reanálisis tras editar. |
| `AI_REANALYZE_ON_CONTENT_CHANGE` | `true` | Restringe reanálisis a título, resumen o contenido. |

No hay API keys de IA en el repositorio ni en esta configuración. Las claves
futuras deben permanecer en variables de Azure App Service o `.env` local no
versionado.

## Flujo automático actual

```text
Article persistido y con id
        ↓
AutomaticAnalysisService
        ↓
ArticleAnalysisService.process_article()
        ↓
AIService
        ↓
ProviderFactory → BaseProvider concreto
        ↓
ArticleAnalysisDTO
        ↓
ArticleAnalysisRepository
        ↓
SQL Server: article_analyses
```

El flujo es correcto respecto al código actual. `ArticleService` primero
persiste el artículo y después llama a `AutomaticAnalysisService`, por lo que
un fallo de IA no revierte la creación. Las rutas web de artículos, la API de
artículos y la integración autenticada de n8n reutilizan este flujo. Los
duplicados de integración retornan su análisis existente y no vuelven a
invocar el provider.

En creación, se requiere título y contenido o resumen. En edición, el
reanálisis es opcional y solo se considera para `title`, `summary` y `content`
cuando está habilitado por configuración. `retry_analysis()` fuerza un nuevo
procesamiento del mismo análisis.

## Datos persistidos y estados

`ArticleAnalysis` conserva:

- resumen, categoría sugerida, dificultad y sentimiento;
- tecnologías y keywords como JSON seguro en columnas de texto;
- provider y modelo usado;
- estado, mensaje de error acotado y `processed_at` UTC;
- marcas de creación y actualización de base de datos.

Los estados definidos son `pending`, `queued`, `processing`, `completed` y
`failed`. La implementación usa `pending` al crear, `processing` antes de
llamar al provider, `completed` al persistir un DTO correcto y `failed` ante
un resultado o excepción fallida. Una fila completada o en procesamiento se
reutiliza salvo que se solicite `force=True`.

## Seguridad y resiliencia actuales

- El provider valida contenido requerido y trunca entrada a 12,000 caracteres
  por defecto.
- `AIService` no expone el mensaje del provider: registra el error y persiste
  solo el nombre de su clase en el DTO fallido.
- `ArticleAnalysis.mark_failed()` limita el diagnóstico persistido a 1,000
  caracteres.
- Repositorio de análisis hace rollback ante fallos de commit.
- El análisis automático captura fallos y devuelve `AutomaticAnalysisResult`
  seguro, evitando romper la creación o edición del artículo.
- No existen timeouts, límites de respuesta ni validación de transporte remoto
  porque no existen clientes remotos todavía.

## Observabilidad y costos

Existe logging de inicio, finalización, reintentos, fallos y persistencia,
además de `provider`, `model_used`, `status`, `processed_at` y error acotado.
No existen conteo de requests, tokens de entrada/salida, latencia por provider,
modelo facturable, presupuesto ni billing. Los nombres de modelos actuales son
metadatos de mocks, no consumo de un servicio externo.

## Capacidades para el asistente editorial

| Capacidad | Estado actual |
| --- | --- |
| Detectar tecnologías y keywords | Ya existe en `ArticleAnalysisDTO`. |
| Sugerir categoría | Ya existe como `suggested_category`; la clasificación RSS también tiene su propio servicio. |
| Resumen de análisis | Ya existe, pero es determinista. |
| Sugerir título | Falta un contrato/DTO específico y provider real. |
| Mejorar o reescribir resumen/contenido | Falta operación editorial y UI de sugerencias. |
| Evaluación editorial | Falta esquema de resultado y criterios. |
| Aplicar cambios al artículo | No existe y debe seguir requiriendo confirmación humana. |

La IA es un asistente editorial: puede analizar, proponer o clasificar. No
puede transicionar un artículo a `published`; `ArticleWorkflowService` sigue
siendo la única autoridad de publicación.

## Asistente editorial efímero

Sprint 8 Entrega 2 incorpora `EditorialSuggestionDTO`, separado de
`ArticleAnalysisDTO`. Contiene título, resumen, contenido y categoría
sugeridos, además de keywords, tecnologías, notas, estado, provider, modelo y
un error seguro. No se guarda en SQL Server.

`EditorialAssistantService.generate_suggestions(article_id)` carga el artículo
y reutiliza `AIService.generate_editorial_suggestions()`. Los providers actuales
heredan una implementación determinista común de `BaseProvider`, por lo que no
duplican lógica ni cambian el contrato de análisis existente.

```text
Editor protegido
  → POST /articles/<id>/editorial-suggestions
  → EditorialAssistantService
  → AIService / Provider
  → EditorialSuggestionDTO JSON efímero
  → JavaScript copia un valor aceptado al formulario
  → Usuario revisa y usa “Guardar cambios”
```

El endpoint requiere login y `articles.edit`. Generar sugerencias no modifica
`Article`, `status`, `published_at` ni `scheduled_publish_at`. Cada botón
“Usar sugerencia” solo actualiza el campo correspondiente en el navegador; el
usuario debe guardar de forma explícita. La categoría se aplica únicamente si
existe una opción activa coincidente. Las keywords se copian al portapapeles,
porque todavía no existe un campo persistente para ellas.

## Revisión editorial efímera

`EditorialReviewService.review_article(article_id)` carga un artículo y usa
`AIService.review_editorial_quality()` para devolver un `EditorialReviewDTO`.
La revisión evalúa claridad, estructura, resumen, coherencia entre título y
contenido, legibilidad, riesgo factual y preparación recomendada. Sus scores
se acotan de 0 a 100 y los niveles se normalizan antes de llegar a la UI.

Esta operación no escribe en SQL Server y no modifica `title`, `summary`,
`content`, `status`, `published_at` ni `scheduled_publish_at`. La preparación
es solo una recomendación de IA: nunca bloquea el workflow editorial y la
decisión final permanece en manos del editor.

```text
Editor con articles.edit
  → POST /articles/<id>/editorial-review
  → EditorialReviewService
  → AIService / Provider
  → EditorialReviewDTO JSON efímero
  → Panel "Revisión editorial IA"
```

`ArticleAnalysis` analiza contenido y puede persistirse; las `Editorial
Suggestions` proponen cambios que una persona acepta en el navegador;
`Editorial Review` solo ofrece una evaluación de calidad. OpenAI reutiliza el
mecanismo de Structured Outputs para ambos contratos sin exponer prompts,
claves ni respuestas crudas al cliente.

## Observabilidad y estado de IA

`AIHealthService` construye `AIHealthStatus` exclusivamente desde configuración
local. El dashboard muestra provider, modelo, estado, análisis automático y
disponibilidad del asistente/revisión editorial sin crear providers ni hacer
llamadas de red. La ausencia de `OPENAI_API_KEY` produce
`configuration_required`; un provider deshabilitado produce `disabled`.

Los conteos del dashboard proceden únicamente de `ArticleAnalysis`, agrupados
por estado en una consulta. Las sugerencias y revisiones editoriales son
efímeras y no se contabilizan como análisis persistidos. OpenAI registra
operación, modelo, latencia y tokens cuando están disponibles, pero tokens,
costos y cuotas no se persisten todavía. Un 429 se trata como fallo seguro;
recordar un estado degradado requeriría persistencia y queda fuera de este
sprint.

## Propuesta concreta para Sprint 8 Entrega 2

1. Definir un DTO de sugerencias editoriales separado de `ArticleAnalysisDTO`.
2. Añadir un caso de uso de solo lectura/generación de sugerencias que reciba
   artículo y objetivo explícito, sin guardar ni modificar `Article`.
3. Reutilizar `AIService` y `ProviderFactory`; incorporar un cliente real solo
   detrás de un provider nuevo o evolucionado con timeout, límite de salida y
   validación estricta del JSON.
4. Exponer las sugerencias únicamente a usuarios autenticados y autorizados,
   presentándolas para aceptación manual en el editor.
5. Diseñar observabilidad mínima para request id, provider, modelo, duración y
   tokens cuando exista un provider remoto.
