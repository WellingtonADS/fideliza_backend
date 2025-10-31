# Fideliza+ API (Backend)

Bem-vindo ao repositório do **Fideliza+**, um sistema de fidelização de clientes desenvolvido com tecnologias modernas para oferecer uma solução robusta e escalável. Este backend fornece suporte completo para as funcionalidades de gestão de clientes, empresas, colaboradores, pontuação e recompensas.

---

## 🧰 Estilo de código e lint

Este projeto inclui configuração para formatação e lint conforme as melhores práticas:

- black (formatação automática)
- ruff (lint e ordenação de imports)

Para usar localmente (no mesmo venv):

```pwsh
pip install -r requirements.txt
ruff check src
black src
```

---

## 📋 Visão Geral

O **Fideliza+** é uma API desenvolvida para gerenciar programas de fidelização de clientes. A aplicação permite que empresas parceiras criem campanhas de pontuação, recompensas e relatórios, enquanto os clientes podem acompanhar seu progresso e resgatar prêmios.

A API foi projetada com foco em segurança, desempenho e extensibilidade, utilizando as melhores práticas de desenvolvimento.

---

## 🚀 Funcionalidades

### **Gestão de Usuários**
- Registro e autenticação de clientes, administradores e colaboradores.
- Suporte a autenticação segura com tokens JWT.

### **Sistema de Pontuação**
- Atribuição e consulta de pontos por empresas parceiras.
- Histórico de transações de pontos.

### **Gestão de Recompensas**
- Criação e listagem de recompensas por empresas.
- Resgate de recompensas com validação de saldo de pontos.

### **Relatórios e Métricas**
- Relatórios resumidos para administradores, incluindo:
  - Total de pontos atribuídos.
  - Total de recompensas resgatadas.

---

## 🛠️ Estrutura do Projeto

A estrutura do projeto está organizada da seguinte forma:

```
src/
├── api/
│   ├── schemas.py          # Definições de schemas (Pydantic)
│   └── v1/
│       ├── __init__.py
│       └── routes.py       # Rotas da API
├── core/
│   ├── config.py           # Configurações principais
│   ├── security.py         # Configurações de segurança (JWT)
│   └── __init__.py
├── database/
│   ├── models.py           # Modelos do banco de dados (SQLAlchemy)
│   ├── session.py          # Configuração da sessão do banco
│   └── __init__.py
└── main.py                 # Ponto de entrada da aplicação
```

---

## 🛠️ Tecnologias Utilizadas

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Base de Dados:** [PostgreSQL](https://www.postgresql.org/)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) (com suporte asyncio)
- **Validação de Dados:** [Pydantic](https://docs.pydantic.dev/)
- **Autenticação:** JWT com python-jose e passlib
- **Servidor:** [Uvicorn](https://www.uvicorn.org/)

---

## 📦 Configuração e Execução (100% local)

### Pré-requisitos
- Python 3.10+
- PostgreSQL local (sem Docker)

### Passos para Configuração (Windows PowerShell)

1. **Clone o repositório:**
   ```pwsh
   git clone https://github.com/wellingtonads/fideliza_backend.git
   cd fideliza_backend
   ```

2. **Crie e ative um ambiente virtual:**
   ```pwsh
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Instale as dependências:**
   ```pwsh
   pip install -r requirements.txt
   ```

4. **Configure as Variáveis de Ambiente:**
   - Crie um arquivo `.env` na raiz do projeto e preencha as variáveis:
     ```env
   DATABASE_URL="postgresql+asyncpg://seu_usuario:sua_senha@localhost:5432/fideliza_db"
     SECRET_KEY="uma_chave_secreta_muito_longa_e_aleatoria_para_os_tokens_jwt"
     ALGORITHM="HS256"
     ACCESS_TOKEN_EXPIRE_MINUTES=30
     ```

5. **Configure a Base de Dados:**
   - Certifique-se de que a base de dados (ex: `fideliza_db`) existe no PostgreSQL.
   - Configure as tabelas utilizando os modelos definidos em `database/models.py`.

6. **Execute a aplicação:**
   ```pwsh
   uvicorn src.main:app --reload
   ```

   A API estará disponível em: http://127.0.0.1:8000

---

## 📖 Documentação

A documentação interativa da API está disponível automaticamente:

- Swagger UI: http://127.0.0.1:8000/api/v1/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

### Documentação do código (MkDocs + mkdocstrings)

Além do Swagger, este repositório inclui um site de documentação do código fonte gerado com **MkDocs** e **mkdocstrings**.

- Configuração: arquivo `mkdocs.yml` na raiz do backend.
- Páginas: pasta `docs/` (inclui referência automática para `src.api.schemas`, `src.api.v1.routes`, `src.core.security` e `src.database.models`).
- Dependências opcionais de docs: `requirements-docs.txt`.

Como rodar localmente (opcional):
1. Instale as dependências (já incluídas em `requirements.txt`): `pip install -r requirements.txt`
2. Inicie o servidor de documentação: `mkdocs serve`
3. Acesse em: `http://127.0.0.1:8000` (ou a porta exibida pelo MkDocs)

---

## 🔐 Autenticação e Recuperação de Senha

- Login: `POST /api/v1/token` (Form URL Encoded: `username`, `password`)
- Recuperar senha: `POST /api/v1/request-password-recovery` (gera link com deep link e web link)
- Redefinir senha: `POST /api/v1/reset-password` (body: `{ token, new_password }`)

Observações:
- JWT inclui claims: `sub`, `user_type`, `company_id`.
- Tokens de recuperação expiram em 15 minutos (`purpose=password-reset`).

---

## 📈 Contribuição

Contribuições são bem-vindas! Siga os passos abaixo para colaborar:

1. Faça um fork do repositório.
2. Crie uma nova branch para sua funcionalidade ou correção:
   ```bash
   git checkout -b minha-nova-funcionalidade
   ```
3. Faça commit das suas alterações:
   ```bash
   git commit -m "Adiciona nova funcionalidade"
   ```
4. Envie para o repositório remoto:
   ```bash
   git push origin minha-nova-funcionalidade
   ```
5. Abra um Pull Request.

---

## 🛡️ Licença

Este projeto está licenciado sob a [Licença MIT](https://opensource.org/licenses/MIT). Sinta-se à vontade para usá-lo e modificá-lo conforme necessário.

---

## 📧 Contato

Para dúvidas ou suporte, entre em contato pelo e-mail: **wellingtonads@example.com**