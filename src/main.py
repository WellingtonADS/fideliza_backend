# fideliza_backend/src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .api.v1.routes import router as api_router
from .database import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando a aplicação...")
    print("Aplicação iniciada com sucesso.")
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")
