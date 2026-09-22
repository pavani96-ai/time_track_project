## Run the app

Install dependencies and start the FastAPI server from this directory:

```bash
uv sync
uv run uvicorn api:app --reload
```

Open <http://127.0.0.1:8000> in a browser. The web interface sends natural-language requests to `POST /api/agent`.

The agent still uses the MCP tools in `main.py`, so set `ANTHROPIC_API_KEY` in `.env` before sending a request. The health check is available at `GET /api/health`.

## Run with Docker

Build and start the container:

```bash
docker build -t timetrack .
docker run --rm -p 8000:8000 -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" timetrack
```

Open <http://127.0.0.1:8000>. The SQLite database is created inside the container at `/app/timetrack.db`.
# time_track_project
# time_track_project
