# HDev AI

HDev AI is an enterprise technical knowledge platform that centralizes articles, RBAC, AI-assisted analysis, and secure n8n RSS automation.

## Problem and solution

Technical information is fragmented. HDev AI imports, deduplicates, analyzes, and governs content in one SQL Server-backed workspace.

## Features and technology

- Article CRUD, categories, sources, dashboard, audits, reports, and QueryRunner.
- Enterprise RBAC with Flask-Login, roles, permissions, and bootstrap protection.
- Provider-agnostic mock AI analysis persisted as one `ArticleAnalysis` per article.
- n8n ingestion secured with `X-API-Key`, validation, and idempotency.
- Python 3.12, Flask 3.x, SQLAlchemy 2.x, Flask-Migrate, SQL Server, Bootstrap 5, Chart.js, and pytest.

## Architecture and automation

`Route → Service → Repository → Model → SQL Server`. Details and Mermaid diagrams: [docs/architecture.md](docs/architecture.md).

`RSS → n8n → Integration API → ArticleService → AutomaticAnalysisService → AIService → ArticleAnalysis`.

## Requirements and installation

Python 3.12, SQL Server with ODBC Driver 17 (or compatible), and optionally n8n.

```powershell
git clone <repository-url>
cd HDev-AI
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
.\venv\Scripts\python.exe -m flask --app app db upgrade
.\venv\Scripts\python.exe -m database.seed_runner
.\venv\Scripts\python.exe app.py
```

Configure every required value in `.env`; never commit it. `SECRET_KEY`, SQL Server settings, and `N8N_API_KEY` are required. The administrator seed additionally requires `HDEV_ADMIN_EMAIL` and `HDEV_ADMIN_PASSWORD`.

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

The suite uses mocks for AI and does not require n8n or an external provider.

## RSS Automation

HDev AI sincroniza fuentes RSS manualmente desde **Fuentes** o de forma diaria
mediante Azure WebJob y `flask sync-rss`. Cada ejecución conserva historial,
deduplicación, análisis IA para artículos nuevos y monitoreo de salud con
alertas internas en el dashboard. Consulta la
[arquitectura RSS](docs/rss_architecture.md) para el flujo, comandos y guía de
diagnóstico.

## Integration and endpoints

The n8n endpoint is `POST /api/integrations/articles`; duplicates are matched by `external_id`, `source_url`, then slug. Documentation: [n8n guide](docs/integrations/n8n.md). The health endpoint is `GET /api/integrations/health`.

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Authenticated dashboard |
| `GET, POST /articles` | Browser article management |
| `POST /api/articles/` | Session/RBAC article API |
| `POST /api/integrations/articles` | API-Key n8n ingestion |

## Structure

```text
ai/ core/ models/ repositories/ services/ routes/
database/ docs/ n8n/ tests/ static/ templates/
```

## Roadmap, screenshots, and license

Planned: background AI processing, provider implementations, observability, CI/CD, and additional sources. Add portfolio screenshots under `docs/images/` before publishing. No license has been selected yet.
