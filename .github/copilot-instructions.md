## Fideliza+ — instruções para agentes (monorepo)

Escopo: 4 projetos no workspace — backend (FastAPI), 2 apps RN (cliente/gestão) e página web de reset. Otimize a produtividade seguindo estes padrões reais do código.

Arquitetura
- Backend (`fideliza_backend`): FastAPI (`src/main.py`), rotas em `src/api/v1/routes.py`, schemas Pydantic em `src/api/schemas.py`.
- DB: SQLAlchemy assíncrono (`postgresql+asyncpg`), models em `src/database/models.py`, sessões em `src/database/session.py` (cria tabelas no startup via `create_db_and_tables`).
- Auth: JWT com claims `sub`, `user_type`, `company_id` (ver `src/core/security.py`); tokenUrl `/api/v1/token`.
- E-mail: FastMail via `.env` (ver `src/core/config.py`).

Fluxos e endpoints (essenciais)
- Login JWT: `POST /api/v1/token` (form urlencoded: `username`, `password`).
- Registro: cliente `POST /api/v1/register/client/` (gera `qr_code_base64` contendo `user.id`); empresa+admin `POST /api/v1/register/company-admin/`.
- Cliente: dashboard `GET /api/v1/dashboard`; pontos `GET /api/v1/points/my-points`; transações `GET /api/v1/points/my-transactions/{company_id}`; recompensas `GET /api/v1/rewards/my-status` e `POST /api/v1/rewards/redeem` (transação de pontos negativa).
- Gestão: empresa do admin `GET/PATCH /api/v1/companies/me` — atenção: `CompanyUpdate.userName` atualiza também `users.name`; colaboradores CRUD em `/collaborators`; pontos `POST /api/v1/points/add` (identificador do cliente = `id` do QR); recompensas CRUD em `/rewards`; relatório `GET /api/v1/reports/summary`.
- Recuperação de senha: `POST /api/v1/request-password-recovery` (token 15min com `purpose=password-reset`, deep links `fidelizacliente://`/`fidelizagestao://` e web links) e `POST /api/v1/reset-password`.

Padrões e gotchas
- Pontos: `PointTransaction.points` positivo = crédito; negativo = resgate. Saldo por empresa = soma filtrada por `company_id`.
- QR Code: `User.generate_qr_code()` grava PNG base64 em `users.qr_code_base64`, conteúdo = `str(user.id)`.
- Segurança: não altere códigos 401/403 sem alinhar interceptores dos apps (401 encerra sessão; 403 mostra aviso).
- DB: use o driver async no `.env` (`DATABASE_URL=postgresql+asyncpg://...`). Engine com `echo=True` — evite log excessivo em testes/CI se ajustar.

Build/test (Windows PowerShell)
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.main:app --reload
pytest -q
```
Apps RN (Android): `npm install` e `npx react-native run-android` (ou task VS Code "Iniciar app no emulador Android"). Base URL em dev (emulador): `http://10.0.2.2:8000/api/v1`.

Arquivos de referência
- Rotas: `src/api/v1/routes.py`
- Schemas: `src/api/schemas.py`
- Models: `src/database/models.py`
- Auth/JWT: `src/core/security.py`
- Config/env: `src/core/config.py`

Se notar divergências (endpoints/claims/flags Android), sinalize para atualizarmos aqui e nos READMEs.
