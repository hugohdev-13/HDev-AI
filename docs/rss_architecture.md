# Arquitectura RSS

## Objetivo

El módulo RSS incorpora contenido técnico desde fuentes confiables sin duplicar
artículos, manteniendo trazabilidad de cada sincronización y salud operativa en
el panel administrativo.

## Flujo

```text
Azure WebJob / POST manual
          |
          v
RSSScheduledSyncService / routes.sources.import_feed
          |
          v
RSSImportService
          |
          v
RSSFeedService
          |
          v
Deduplicación
          |
          v
ArticleService
          |
          v
IA / Clasificación
          |
          v
Azure SQL
          |
          v
RSSSyncHistory
          |
          v
RSSSourceHealthService
          |
          v
Dashboard / Alertas RSS
```

## Sincronización manual y automática

El botón **Sincronizar ahora** realiza un `POST` a la ruta existente de la
fuente y reutiliza `RSSImportService`. El proceso automático no vive dentro de
Flask ni Gunicorn: un Azure WebJob ejecuta el comando siguiente una vez al día:

```powershell
.\venv\Scripts\python.exe -m flask --app app.py sync-rss
```

`RSSScheduledSyncService` obtiene únicamente fuentes activas de tipo RSS y
aisla los errores por fuente para que un fallo no detenga el resto del lote.

## Deduplicación e IA

Antes de crear un artículo, la importación identifica duplicados por los
identificadores del feed y URL de origen. Los duplicados no vuelven a invocar
`ArticleService.create_article_with_analysis()`, por lo que no consumen IA.
Los artículos nuevos conservan el flujo actual de análisis y clasificación.

## Historial, salud y alertas

Cada ejecución manual o automática registra un `RSSSyncHistory` con estado,
contadores, duración y mensaje operacional. `RSSSourceHealthService` calcula
la salud sin persistir una tabla adicional:

- `healthy`: última ejecución correcta y sin fallos consecutivos.
- `warning`: ejecución parcial, uno o dos fallos o fuente retrasada.
- `critical`: tres o más fallos consecutivos.
- `never_synced`: no existe historial.

El dashboard muestra el resumen de salud, un indicador global RSS y alertas
internas solamente para estados `warning` y `critical`. Los mensajes se
sanean, se limitan a una línea corta y no muestran stack traces ni secretos.

## Comandos importantes

```powershell
.\venv\Scripts\python.exe -m flask --app app.py sync-rss
.\venv\Scripts\python.exe -m flask --app app.py db upgrade
.\venv\Scripts\python.exe -m pytest -v
```

## Troubleshooting básico

1. Abra **Fuentes → Historial de sincronizaciones** y confirme el último
   resultado de la fuente.
2. Revise el dashboard: una alerta crítica indica tres o más fallos seguidos.
3. Compruebe que la fuente esté activa, sea de tipo RSS y tenga un `feed_url`
   HTTP(S) válido.
4. Ejecute `sync-rss` manualmente desde el servidor para aislar problemas del
   WebJob.
5. Consulte logs protegidos de Azure para el diagnóstico técnico; el panel no
   expone cadenas de conexión, credenciales ni trazas completas.
