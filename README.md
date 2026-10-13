# Configuration Precedence API

A small FastAPI service for the configuration-precedence assignment.

## Precedence

1. Hardcoded defaults
2. `config.<APP_ENV>.yaml` (defaults to `config.development.yaml`)
3. `.env` (supports `NUM_WORKERS` as an alias for `workers`)
4. OS environment variables beginning with `APP_`
5. Repeated `set=key=value` query parameters

`api_key` is always masked as `****` in responses. CORS is enabled for browser-based grading.

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:APP_WORKERS = "7"
$env:APP_DEBUG = "false"
$env:APP_LOG_LEVEL = "warning"
$env:APP_API_KEY = "key-7f0mmqot15"
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/effective-config` in your browser. The default response should be equivalent to:

```json
{"port":8000,"workers":7,"debug":false,"log_level":"warning","api_key":"****"}
```

Test CLI overrides at `http://127.0.0.1:8000/effective-config?set=port=9000&set=debug=true&set=workers=2`.

## Deploy on Render

The included `render.yaml` defines a free Python web service and the assignment's OS-level `APP_*` variables. Put these files in a GitHub repository, then in Render choose **New + → Blueprint** and connect that repository. Render reads `render.yaml` to create and deploy the service. The service start command uses Render's `$PORT` while the response's `port` config value remains the assignment's logical config value.

After deployment, submit the base URL ending in `/effective-config`, without query parameters. Example shape: `https://YOUR-SERVICE.onrender.com/effective-config`.

The API key values in this exercise are assignment-provided sample values. Do not commit real secrets to a public repository.
