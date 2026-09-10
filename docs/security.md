# Seguridad de sesión y CSRF

## CSRF para sesiones de navegador

HDev AI usa `Flask-WTF` y `CSRFProtect` como protección global. Todo método
que modifica estado y usa la sesión del navegador debe enviar un token válido.
El layout privado publica el token en un meta tag y `static/js/app.js` lo añade
a formularios POST que no tengan un token explícito. Login y logout incluyen
un campo oculto explícito.

Las operaciones fetch del asistente y revisión editorial usan el header
`X-CSRFToken`. Los fallos CSRF devuelven una página 400 segura para HTML o un
JSON seguro para solicitudes que declaran `Accept: application/json`; no se
revela el token esperado.

## Logout y cookies

Logout es exclusivamente `POST /auth/logout`, requiere login y CSRF. Un GET
recibe 405 y no modifica sesión. En producción, las cookies de sesión son
`HttpOnly`, `Secure` y `SameSite=Lax`. Desarrollo y pruebas mantienen cookies
compatibles con HTTP local.

## Integraciones machine-to-machine

Solo el blueprint `/api/integrations` está exento de CSRF porque no usa
sesiones de navegador y exige `X-API-Key` con comparación constante. La
exención es explícita en `app.py`; no se aplica a APIs autenticadas por sesión.
`N8N_INTEGRATION_ENABLED=false` deshabilita esa integración incluso si existe
una clave.

## Configuración de producción

El arranque de producción falla si falta `SECRET_KEY`, o si falta
`N8N_API_KEY` mientras `N8N_INTEGRATION_ENABLED=true`. La configuración de
base de datos ya valida driver, servidor, base y credenciales SQL cuando
corresponde. No se deben versionar valores reales en `.env`.
