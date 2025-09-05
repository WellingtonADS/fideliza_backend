# fideliza_backend/src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Importar o router das rotas da API
from .api.v1.routes import router

# 1. IMPORTAR A FUNÇÃO PARA CRIAR AS TABELAS
from .database.session import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando a aplicação...")
    # 2. CHAMAR A FUNÇÃO PARA CRIAR AS TABELAS NO ARRANQUE
    await create_db_and_tables()
    print("Tabelas da base de dados verificadas/criadas.")
    print("Aplicação iniciada com sucesso.")
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API Fideliza+! Consulte /docs para mais informações."}

# Incluir o router na aplicação principal
app.include_router(router, prefix="/api/v1")
