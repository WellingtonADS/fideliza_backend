# **Fideliza+ API (Backend)**

Bem-vindo ao repositório do **Fideliza+**, um sistema de fidelização de clientes desenvolvido com tecnologias modernas para oferecer uma solução robusta e escalável. Este backend fornece suporte completo para as funcionalidades de gestão de clientes, empresas, colaboradores, pontuação e recompensas.

---

## **📋 Visão Geral**

O **Fideliza+** é uma API desenvolvida com o objetivo de gerenciar programas de fidelização de clientes. A aplicação permite que empresas parceiras criem campanhas de pontuação, recompensas e relatórios, enquanto os clientes podem acompanhar seu progresso e resgatar prêmios.

A API foi projetada com foco em segurança, desempenho e extensibilidade, utilizando as melhores práticas de desenvolvimento.

---

## **🚀 Funcionalidades**

### **Gestão de Usuários**
- Registro e autenticação de clientes, administradores e colaboradores.
- Suporte a autenticação segura com tokens JWT.
- Geração de QR Codes para identificação de clientes.

### **Sistema de Pontuação**
- Atribuição de pontos a clientes por empresas parceiras.
- Consulta de saldo de pontos agrupados por empresa.
- Histórico de transações de pontos.

### **Gestão de Recompensas**
- Criação e listagem de recompensas por empresas.
- Resgate de recompensas com validação de saldo de pontos.
- Registro de histórico de recompensas resgatadas.

### **Relatórios e Métricas**
- Relatórios resumidos para administradores, incluindo:
  - Total de pontos atribuídos.
  - Total de recompensas resgatadas.
  - Número de clientes únicos.

### **Experiência do Cliente**
- Listagem de empresas parceiras.
- Dashboard com resumo de pontos e últimas atividades.

---

## **🛠️ Tecnologias Utilizadas**

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Base de Dados:** [PostgreSQL](https://www.postgresql.org/)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) (com suporte asyncio)
- **Validação de Dados:** [Pydantic](https://docs.pydantic.dev/)
- **Autenticação:** JWT com python-jose e passlib
- **Servidor:** [Uvicorn](https://www.uvicorn.org/)

---

## **📦 Configuração e Execução**

### **Pré-requisitos**
- Python 3.10+
- PostgreSQL configurado localmente ou em um container Docker.

### **Passos para Configuração**

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/wellingtonads/fideliza_backend.git
   cd fideliza_backend
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as Variáveis de Ambiente:**
   - Crie um ficheiro .env na raiz do projeto e preencha as seguintes variáveis:
     ```env
     DATABASE_URL="postgresql+asyncpg://seu_usuario:sua_senha@localhost:5432/fideliza_db"
     SECRET_KEY="uma_chave_secreta_muito_longa_e_aleatoria_para_os_tokens_jwt"
     ALGORITHM="HS256"
     ACCESS_TOKEN_EXPIRE_MINUTES=30
     ```

5. **Configure a Base de Dados:**
   - Certifique-se de que a base de dados (ex: fideliza_db) existe no seu PostgreSQL.
   - Execute o script fideliza_db.sql para criar todas as tabelas e conceder as permissões necessárias ao seu utilizador.

### **Executar a Aplicação**

Para iniciar a aplicação, execute o seguinte comando:

```bash
uvicorn src.main:app --reload
```

A API estará disponível em [http://127.0.0.1:8000](http://127.0.0.1:8000).

### **Aceder à Documentação Interativa**

Para interagir e testar todos os endpoints, aceda à documentação automática gerada pelo FastAPI:

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---


*Este projeto foi desenvolvido com o apoio e a orientação da IA da Google.*