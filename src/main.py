
# fideliza_backend/src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi.responses import PlainTextResponse

# Importar o router das rotas da API
from .api.v1.routes import router, limiter

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

app = FastAPI(
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

# Configurar SlowAPI globalmente usando a mesma instância do router
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: PlainTextResponse("Muitas requisições. Tente novamente mais tarde.", status_code=429))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://10.0.2.2:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API Fideliza+! Consulte /docs para mais informações."}

# Incluir o router na aplicação principal
app.include_router(router, prefix="/api/v1")
