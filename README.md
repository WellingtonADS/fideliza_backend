# Fideliza+ API

API backend para o sistema de fidelização de clientes "Fideliza+". Desenvolvido com FastAPI e SQLAlchemy.

## Estrutura do Projeto

A estrutura principal do projeto reside na pasta `src/`:

- `src/main.py`: Ponto de entrada da aplicação FastAPI.
- `src/core/`: Configurações centrais, segurança e gestão de tokens.
- `src/database/`: Modelos de dados (SQLAlchemy), sessão e inicialização da base de dados.
- `src/api/`: Definição dos schemas (Pydantic) e rotas da API (endpoints).

## Como Executar

1.  **Instalar dependências:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configurar o ambiente:**
    - Crie um ficheiro `.env` na raiz do projeto com base no ficheiro `.env.example`.
    - Preencha as variáveis de ambiente, como `DATABASE_URL` e `SECRET_KEY`.

3.  **Executar a aplicação:**
    ```bash
    uvicorn src.main:app --reload
    ```