# Production readiness — Sprint 9 Entrega 1

## Estado general

HDev AI tiene una base funcional sólida para producción: rutas privadas con
Flask-Login y RBAC, consultas ORM parametrizadas, migraciones lineales, health
checks, cookies seguras en producción y flujos RSS/IA que evitan mutar el
workflow editorial. No debe declararse v1.0 hasta resolver los blockers de
CSRF y operación programada.

## Hallazgos

| Severity | Área | Hallazgo | Riesgo | Acción | Estado |
| --- | --- | --- | --- | --- | --- |
| Resuelto 9.2 | CSRF | CSRFProtect global cubre mutaciones con sesión; formularios y fetch reciben token. | Reduce envíos cross-site no autorizados. | Mantener tokens al agregar nuevos POST/fetch. | Resuelto |
| BLOCKER v1.0 | Automatización | `publish-scheduled` requiere scheduler externo; no se confirmó una programación Azure. | Artículos aprobados pueden quedar sin publicar. | Configurar y monitorizar Azure WebJob/cron externo antes del despliegue v1.0. | Pendiente operación Azure |
| Resuelto 9.2 | Configuración | Producción valida `SECRET_KEY` y `N8N_API_KEY` si n8n está habilitado. | Evita arranques inseguros o incompletos. | Mantener variables en Azure App Settings. | Resuelto |
| Resuelto 9.2 | Logout | Logout usa POST con login y CSRF. | Evita mutación de sesión mediante GET. | Mantener navegación basada en formulario. | Resuelto |
| MEDIUM | Headers | No hay CSP; las protecciones base no sustituyen una política de scripts. | Reduce defensa frente a XSS si se introduce HTML no confiable. | Diseñar CSP con nonces y revisar Bootstrap/Chart.js/JS externo antes de activarla. | Pendiente 9.3 |
| MEDIUM | Health check | `/health/database` no requiere autenticación. | Divulga disponibilidad de base de datos a quien conozca la URL. | Restringirlo por red/plataforma o proteger readiness interno según Azure. | Pendiente operación Azure |
| MEDIUM | Dependencias | `requirements.txt` mezcla paquetes de runtime con herramientas de desarrollo y paquetes potencialmente no usados (`Django`, `celery`, `virtualenv`). | Superficie de actualización y despliegue mayor. | Auditoría de uso y separar requirements de producción/desarrollo sin cambios masivos. | Pendiente 9.3 |
| LOW | Código | Algunos módulos RSS/rutas conservan formato compacto de múltiples instrucciones por línea. | Mantenibilidad y revisión de seguridad más difíciles. | Formatear de forma mecánica en una entrega dedicada con cobertura existente. | Post-v1.0 o 9.4 |
| LOW | Observabilidad IA | No se persisten tokens, costos ni el último rate limit. | No hay tendencias históricas de cuota/costo. | Diseñar telemetría persistida aprobada, sin secretos ni precios hardcodeados. | Post-v1.0 |

## Correcciones realizadas en esta entrega

- Se añadieron `X-Content-Type-Options`, `Referrer-Policy` y
  `Permissions-Policy`; HSTS se aplica solo con `APP_ENV=production`.
- El health check de base de datos registra únicamente el tipo de excepción,
  no el traceback potencialmente sensible.
- La descarga RSS ya no sigue redirects automáticamente: valida cada URL de
  destino con la misma protección SSRF y limita los saltos a cuatro.
- CSRF global con Flask-WTF, logout POST y validación fail-fast de producción.

## Verificaciones de seguridad

- **Secretos:** `.env` está ignorado y `.env.example` no contiene valores. La
  revisión no encontró secretos versionados; los valores de prueba están
  limitados a tests/documentación.
- **Autenticación/autorización:** artículos, categorías, fuentes, dashboard,
  preview, scheduling y operaciones IA usan login más permisos; integración
  n8n usa API key. El bypass administrativo RBAC sigue limitado al bootstrap.
- **XSS:** no se detectó `|safe` en templates. Jinja autoescape permanece
  activo y las salidas de IA/RSS se renderizan como texto. La futura CSP sigue
  siendo recomendable.
- **SQL/ORM:** consultas de aplicación usan ORM/SQLAlchemy parametrizado. El
  único ejecutor SQL genérico es `database/query_runner.py`, herramienta de
  administración que requiere que el autor provea la consulta; no se expone
  por rutas HTTP.
- **SSRF:** se bloquean esquemas no HTTP(S), localhost, IPs privadas,
  loopback, link-local y redirects a dichos destinos. La mitigación depende de
  DNS al momento de validación; una protección de egress/red sigue siendo
  recomendada en Azure.
- **Open redirects:** `next` se limita a mismo host y las demás redirecciones
  usan `url_for`.
- **Uploads:** no existe carga física de archivos; las imágenes se tratan como
  URLs y no hay almacenamiento de uploads que auditar.

## Operación y plataforma

`/health` es un liveness check seguro. `/health/database` realiza solo
`SELECT 1`; no llama IA ni RSS. Las migraciones forman una única cadena con
head `8fabb4b92a92`. `sync-rss` y `publish-scheduled` son comandos diseñados
para scheduler externo; la configuración real del scheduler es requisito de
operación antes de v1.0.

La IA conserva API keys solo en backend, Structured Outputs, timeout y DTOs de
fallo seguro. Una cuota/429 es un fallo externo controlado, no un error de
workflow ni un HTTP 500 del dashboard.

## Propuesta exacta para Entrega 9.2

Implementar protección CSRF global con inventario de formularios, tokens en
templates y cabeceras para fetch; convertir logout a POST; añadir validación
fail-fast de configuración obligatoria exclusivamente en producción; y agregar
pruebas de regresión de formularios, APIs autenticadas y configuración. No
mezclar estos cambios con CSP, SEO profundo o telemetría de costos.
