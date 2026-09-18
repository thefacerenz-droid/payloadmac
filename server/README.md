# Backend

Copy `.env.example` to `.env`, set values, install dependencies, then run:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
```

On Windows replace `.venv/bin/` with `.venv\\Scripts\\`. Production needs a persistent WebSocket-capable host and TLS proxy. API calls need `Authorization: Bearer ADMIN_TOKEN`; agents connect to `/agent?token=ADMIN_TOKEN`. Device state is intentionally in memory, so restart clears the list.
