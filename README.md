# **Fideliza+ API (Backend)**

Bem-vindo ao repositório do backend do **Fideliza+**, um sistema de fidelização de clientes construído com tecnologias modernas, rápidas e robustas.

## **milestone Marco de Projeto: Conclusão da Fase 2**

Este repositório reflete a conclusão bem-sucedida da **Fase 2: Gestão de Recompensas e Visibilidade Expandida**. Todas as funcionalidades essenciais para o ciclo de vida de pontos e prémios estão implementadas, testadas e estáveis.

### **Funcionalidades da Fase 1 (MVP \- Concluído)**

* Gestão completa de Utilizadores (Clientes, Admins, Colaboradores).  
* Autenticação segura com tokens JWT.  
* Sistema de atribuição de pontos.  
* Consulta de saldo de pontos pelo cliente.

### **✨ Novas Funcionalidades da Fase 2 (Concluído)**

* **Gestão de Prémios:**  
  * POST /rewards/: Endpoint para Administradores criarem prémios (recompensas) com um custo de pontos definido.  
  * GET /rewards/: Endpoint para Administradores e Colaboradores listarem os prémios da sua empresa.  
* **Visibilidade para o Cliente:**  
  * GET /rewards/my-status: Endpoint para o cliente ver todos os prémios das empresas onde tem pontos, com o estado (redeemable) e os pontos em falta para cada um.  
* **Ciclo de Resgate de Prémios:**  
  * POST /rewards/redeem: Endpoint para o cliente "gastar" os seus pontos e resgatar um prémio. A lógica deduz os pontos do saldo do cliente e regista o resgate.

## **🛠️ Tecnologias Utilizadas**

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)  
* **Base de Dados:** [PostgreSQL](https://www.postgresql.org/)  
* **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) (com suporte asyncio)  
* **Validação de Dados:** [Pydantic](https://www.google.com/search?q=https://docs.pydantic.dev/)  
* **Autenticação:** JWT com python-jose e passlib

## **🚀 Como Executar o Projeto Localmente**

### **1\. Pré-requisitos**

* Python 3.10+  
* PostgreSQL a correr localmente ou num container Docker.

### **2\. Configuração do Ambiente**

1. **Clone o repositório:**  
   git clone https://github.com/wellingtonads/fideliza\_backend.git  
   cd fideliza\_backend

2. **Crie e ative um ambiente virtual:**  
   \# Windows  
   python \-m venv venv  
   .\\venv\\Scripts\\Activate.ps1

3. **Instale as dependências:**  
   pip install \-r requirements.txt

4. **Configure as Variáveis de Ambiente:**  
   * Crie um ficheiro .env na raiz do projeto e preencha as seguintes variáveis:  
     DATABASE\_URL="postgresql+asyncpg://seu\_usuario:sua\_senha@localhost:5432/fideliza\_db"  
     SECRET\_KEY="uma\_chave\_secreta\_muito\_longa\_e\_aleatoria\_para\_os\_tokens\_jwt"  
     ALGORITHM="HS256"  
     ACCESS\_TOKEN\_EXPIRE\_MINUTES=30

5. **Configure a Base de Dados:**  
   * Certifique-se de que a base de dados (fideliza\_db no exemplo) existe.  
   * Execute o script fideliza\_db.sql para criar todas as tabelas e conceder as permissões necessárias.

### **3\. Executar a Aplicação**

uvicorn src.main:app \--reload

A API estará disponível em http://127.0.0.1:8000.

### **4\. Aceder à Documentação**

Para interagir e testar os endpoints, aceda à documentação automática:

* **Swagger UI:** http://127.0.0.1:8000/docs

## **🔮 Próximos Passos (Fase 3\)**

O próximo grande marco de desenvolvimento é a **Fase 3: Relatórios e Melhorias Contínuas**, que incluirá:

* **Entregável 3.1:** Serviço de Relatórios e Estatísticas para os Administradores.  
* **Entregável 3.2:** Aprimoramento da Gestão de Utilizadores (edição e exclusão).  
* **Entregável 3.3:** Otimizações de performance e preparação para o ambiente de produção.

*Este projeto foi desenvolvido com o apoio e a orientação da IA da Google.*