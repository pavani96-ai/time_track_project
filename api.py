from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from client import run_agent_loop


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class AgentResponse(BaseModel):
    response: str


app = FastAPI(title="TimeTrack Agent API")
frontend_path = Path(__file__).parent / "static" / "index.html"


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/agent", response_model=AgentResponse)
async def run_agent(request: AgentRequest) -> AgentResponse:
    try:
        response = await run_agent_loop(request.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AgentResponse(response=response)


@app.get("/", response_class=FileResponse)
async def frontend() -> str:
    return str(frontend_path)