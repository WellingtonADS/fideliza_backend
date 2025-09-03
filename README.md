# **Fideliza+ API (Backend)**

Bem-vindo ao repositório do **Fideliza+**, um sistema de fidelização de clientes desenvolvido com tecnologias modernas para oferecer uma solução robusta e escalável. Este backend fornece suporte completo para as funcionalidades de gestão de clientes, empresas, colaboradores, pontuação e recompensas.

---

## **📋 Visão Geral**

O **Fideliza+** é uma API desenvolvida para gerenciar programas de fidelização de clientes. A aplicação permite que empresas parceiras criem campanhas de pontuação, recompensas e relatórios, enquanto os clientes podem acompanhar seu progresso e resgatar prêmios.

A API foi projetada com foco em segurança, desempenho e extensibilidade, utilizando as melhores práticas de desenvolvimento.

---

## **🚀 Funcionalidades**

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

## **🛠️ Estrutura do Projeto**

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
   - Crie um arquivo `.env` na raiz do projeto e preencha as variáveis:
     ```env
     DATABASE_URL="postgresql+asyncpg://seu_usuario:sua_senha@:5432/fideliza_db"
     SECRET_KEY="uma_chave_secreta_muito_longa_e_aleatoria_para_os_tokens_jwt"
     ALGORITHM="HS256"
     ACCESS_TOKEN_EXPIRE_MINUTES=30
     ```

5. **Configure a Base de Dados:**
   - Certifique-se de que a base de dados (ex: `fideliza_db`) existe no PostgreSQL.
   - Configure as tabelas utilizando os modelos definidos em `database/models.py`.

6. **Execute a aplicação:**
   ```bash
   uvicorn src.main:app --reload
   ```

   A API estará disponível em: [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## **📖 Documentação**

A documentação interativa da API está disponível automaticamente:

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI JSON:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## **🌐 Status de Operação**

O projeto está atualmente em operação na plataforma [Render](https://render.com):

- **Serviço Web:**
  - URL: [https://fideliza-backend.onrender.com](https://fideliza-backend.onrender.com)
  - Branch: `main`
  - Tipo de instância: Gratuita

- **Base de Dados:**
  - Nome: `fideliza-db`
  - Status: Disponível
  - Expiração: 28 de setembro de 2025 (salvo upgrade para instância paga)

---

## **📈 Contribuição**

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

## **🛡️ Licença**

Este projeto está licenciado sob a [Licença MIT](https://opensource.org/licenses/MIT). Sinta-se à vontade para usá-lo e modificá-lo conforme necessário.

---

## **📧 Contato**

Para dúvidas ou suporte, entre em contato pelo e-mail: **wellingtonads@example.com**