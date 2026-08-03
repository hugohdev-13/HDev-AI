# Integración n8n

El workflow importa elementos RSS y los envía a HDev AI sin sesión de navegador. El flujo es: `Manual Trigger → RSS Read → Edit Fields → Create Article`.

Importa [hdev-ai-rss-import.json](../../n8n/workflows/hdev-ai-rss-import.json) desde **Workflows → Import from File**. Sustituye `CHANGE_ME_API_KEY` y selecciona una URL RSS. Para Flask en Windows y n8n Docker usa `http://host.docker.internal:5000/api/integrations/articles`.

El nodo HTTP Request usa `POST`, `Content-Type: application/json` y `X-API-Key`. Envía `title` y al menos `summary` o `content`; conserva el GUID/enlace RSS como `external_id` para idempotencia.

Una creación devuelve `201`; una repetición devuelve `200` con `duplicate: true`. Payload inválido devuelve `400` y clave ausente o incorrecta `401`. `GET /api/integrations/health` comprueba conectividad con la misma clave.

```powershell
$headers = @{ "X-API-Key" = $env:N8N_API_KEY }
$body = Get-Content docs\integrations\examples\article_payload.json -Raw
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/integrations/articles -Headers $headers -ContentType application/json -Body $body
```

Tras una prueba manual exitosa, reemplaza Manual Trigger por Schedule Trigger y define la periodicidad. El workflow exportado no contiene secretos.
