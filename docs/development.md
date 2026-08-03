# Development commands

Run from `C:\Users\hugoh\HDev-AI`.

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
.\venv\Scripts\python.exe -m flask --app app db upgrade
.\venv\Scripts\python.exe -m database.seed_runner
.\venv\Scripts\python.exe -m pytest -v
.\venv\Scripts\python.exe -m database.scripts.reports
.\venv\Scripts\python.exe -m database.scripts.diagnostics
.\venv\Scripts\python.exe -m pip freeze > requirements.txt
```

For n8n: `docker run --rm -it -p 5678:5678 -v ${PWD}\n8n\data:/home/node/.n8n n8nio/n8n`. Use `docker logs <container-id>` to inspect logs. With Flask on Windows, n8n Docker requests `http://host.docker.internal:5000`.
