"""Echo server: returns whatever message the client sends."""
import logging

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [echo-server] %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(title="Echo server")


class EchoRequest(BaseModel):
    message: str


class EchoResponse(BaseModel):
    echo: str


@app.post("/echo", response_model=EchoResponse)
def echo(req: EchoRequest) -> EchoResponse:
    log.info("received message=%r", req.message)
    return EchoResponse(echo=req.message)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
