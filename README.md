Fideliza+ API (Backend)
Bem-vindo ao repositório do backend do Fideliza+, um sistema de fidelização de clientes construído com tecnologias modernas, rápidas e robustas.

Este projeto representa a conclusão bem-sucedida da Fase 1 (MVP), fornecendo a base completa para a gestão de utilizadores, empresas e o sistema de pontuação.

✨ Funcionalidades (Marco MVP Concluído)
Gestão de Utilizadores:

Registo de Clientes com geração automática de QR Code.

Registo de Empresas com um utilizador Administrador inicial.

Registo de Colaboradores por um Administrador.

Autenticação Segura:

Sistema de login baseado em token JWT (OAuth2).

Hash seguro de senhas utilizando passlib e bcrypt.

Sistema de Pontuação:

Endpoint protegido para que Administradores e Colaboradores possam atribuir pontos a um cliente.

Endpoint para que os Clientes possam consultar o seu saldo de pontos, agrupado por empresa.

Segregação de Dados: A arquitetura garante que cada empresa só pode aceder e gerir os seus próprios dados (colaboradores e transações de pontos).

Documentação Automática: Acesso à documentação interativa da API (Swagger UI e ReDoc).

🛠️ Tecnologias Utilizadas
Framework: FastAPI

Base de Dados: PostgreSQL

ORM: SQLAlchemy (com suporte asyncio)

Validação de Dados: Pydantic

Autenticação: JWT com python-jose e passlib

🚀 Como Executar o Projeto Localmente
Siga estes passos para configurar e executar a aplicação no seu ambiente de desenvolvimento.

1. Pré-requisitos
Python 3.10+

PostgreSQL a correr localmente ou num container Docker.

2. Configuração do Ambiente
Clone o repositório:

git clone https://github.com/wellingtonads/fideliza_backend.git
cd fideliza_backend

Crie e ative um ambiente virtual:

# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

Instale as dependências:

pip install -r requirements.txt

Configure as Variáveis de Ambiente:

Crie uma cópia do ficheiro .env.example (se existir) ou crie um novo ficheiro chamado .env na raiz do projeto.

Preencha as seguintes variáveis:

# Exemplo de .env
DATABASE_URL="postgresql+asyncpg://seu_usuario:sua_senha@localhost:5432/fideliza_db"
SECRET_KEY="uma_chave_secreta_muito_longa_e_aleatoria_para_os_tokens_jwt"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

Configure a Base de Dados:

Certifique-se de que a base de dados (fideliza_db no exemplo acima) existe no seu PostgreSQL.

Execute o script fideliza_db.sql para criar todas as tabelas e conceder as permissões necessárias.

3. Executar a Aplicação
Com o ambiente virtual ativado, execute o seguinte comando:

uvicorn src.main:app --reload

A API estará agora disponível em http://127.0.0.1:8000.

4. Aceder à Documentação
Para interagir e testar os endpoints, aceda à documentação automática gerada pelo FastAPI:

Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

Próximos Passos (Fase 2)
O próximo grande marco de desenvolvimento é a Fase 2: Gestão de Recompensas e Visibilidade Expandida, que incluirá:

Endpoints para que os Administradores possam criar e gerir prémios.

Lógica para notificar os clientes quando atingem a pontuação necessária.

Endpoints para o resgate de prémios.

Este projeto foi desenvolvido com o apoio e a orientação da IA da Google.