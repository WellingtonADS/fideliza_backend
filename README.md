# **Fideliza+ API (Backend) \- Versão 1.0**

Bem-vindo ao repositório do backend do **Fideliza+**, um sistema de fidelização de clientes construído com tecnologias modernas, rápidas e robustas.

## **M A R C O  D E  P R O J E T O: Desenvolvimento do Backend**

Este repositório representa a **conclusão bem-sucedida de todas as fases de desenvolvimento planeadas para o backend (Fases 1, 2 e 3\)**. A API está completa, funcional e estável, fornecendo todas as funcionalidades necessárias para suportar as aplicações móveis do cliente e do administrador.

## **✨ Funcionalidades Implementadas**

### **Fase 1: Core System (MVP)**

* **Gestão de Utilizadores:** Registo de Clientes (com QR Code), Empresas (com Admin) e Colaboradores.  
* **Autenticação Segura:** Sistema de login com tokens JWT (OAuth2) e hash de senhas.  
* **Sistema de Pontuação:** Endpoints para atribuir pontos e para clientes consultarem o seu saldo.

### **Fase 2: Gestão de Recompensas e Visibilidade**

* **Gestão de Prémios:** Endpoints para Admins criarem e listarem os prémios da sua empresa.  
* **Visibilidade para o Cliente:** Endpoint para o cliente ver o seu progresso para alcançar cada prémio.  
* **Ciclo de Resgate:** Lógica completa para um cliente resgatar um prémio, com a dedução automática dos pontos.

### **Fase 3: Relatórios e Melhorias**

* **Relatórios para Admins:** Endpoint que fornece um relatório resumido com as principais métricas de desempenho (pontos atribuídos, prémios resgatados, clientes únicos).  
* **Gestão Completa de Colaboradores:** Endpoints para Admins listarem, atualizarem e excluírem os seus colaboradores.  
* **Otimizações de Performance:** Refatoração de consultas para maior eficiência e prevenção do problema "N+1".

## **🛠️ Tecnologias Utilizadas**

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)  
* **Base de Dados:** [PostgreSQL](https://www.postgresql.org/)  
* **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) (com suporte asyncio)  
* **Validação de Dados:** [Pydantic](https://www.google.com/search?q=https://docs.pydantic.dev/)  
* **Autenticação:** JWT com python-jose e passlib  
* **Servidor:** [Uvicorn](https://www.uvicorn.org/)

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
   * Certifique-se de que a base de dados (ex: fideliza\_db) existe no seu PostgreSQL.  
   * Execute o script fideliza\_db.sql para criar todas as tabelas e conceder as permissões necessárias ao seu utilizador.

### **3\. Executar a Aplicação**

uvicorn src.main:app \--reload

A API estará disponível em http://127.0.0.1:8000.

### **4\. Aceder à Documentação Interativa**

Para interagir e testar todos os endpoints, aceda à documentação automática gerada pelo FastAPI:

* **Swagger UI:** http://127.0.0.1:8000/docs

## **🔮 Próximas Fases do Projeto**

Com o backend completo, o foco do desenvolvimento agora transita para a **Camada de Apresentação**:

* **Fase 4:** Desenvolvimento do Aplicativo Móvel do Cliente em React Native.  
* **Fase 5:** Desenvolvimento do Aplicativo Móvel de Gestão (Admin/Colaborador) em React Native.

*Este projeto foi desenvolvido com o apoio e a orientação da IA da Google.*