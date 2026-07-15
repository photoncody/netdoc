# AGENTS.md

## Cursor Cloud specific instructions

NetDoc is a single-service Python/FastAPI app (`app/main.py`) that serves both the REST API and the static Vue web UI, backed by an embedded SQLite DB. There are no other backing services. See `README.md` for the standard commands; the notes below cover only non-obvious caveats.

### Database path caveat (important)
The default DB URL is `sqlite:////data/netdoc.db` (an absolute `/data` path from the Docker image) which is not writable in the dev VM. `app/main.py` calls `create_all` at import time, so this breaks both `pytest` and `uvicorn` unless you override the path. Always set `NETDOC_DB_URL` to a writable location:

- Run tests: `NETDOC_DB_URL="sqlite:///./test_netdoc.db" python3 -m pytest`
- Run dev server: `NETDOC_DB_URL="sqlite:///./netdoc_dev.db" python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

(`*.db` files are gitignored.)

### Other notes
- Console scripts (`uvicorn`, `pytest`) install to `~/.local/bin`, which is not on PATH. Invoke them via `python3 -m uvicorn` / `python3 -m pytest`.
- On startup you'll see `Warning: Could not create upload directory /data/uploads`. This is non-fatal; only device image uploads are affected. To exercise uploads locally, make `/data` writable.
- There is no linter configured in this repo (no ruff/flake8/black config). The app targets Python 3.11 but runs fine on the VM's Python 3.12.
- Auth is off unless both `NETDOC_USER` and `NETDOC_PASSWORD` are set; the API is fully open otherwise.
