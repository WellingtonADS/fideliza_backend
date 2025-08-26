# fideliza_backend/src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

# CORREÇÃO: Importar 'router' diretamente, sem renomear
from .api.v1.routes import router

from .database import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando a aplicação...")
    print("Aplicação iniciada com sucesso.")
    yield

app = FastAPI(lifespan=lifespan)

# CORREÇÃO: Utilizar o objeto 'router' que foi importado
app.include_router(router, prefix="/api/v1")