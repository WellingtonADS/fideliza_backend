-- Cria a tabela para armazenar as empresas
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    admin_user_id INTEGER, -- Será definida como chave estrangeira mais tarde para evitar dependência circular
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Cria a tabela para armazenar todos os tipos de usuários (Clientes, Admins, Colaboradores)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    qr_code_base64 TEXT,
    user_type VARCHAR(50) NOT NULL DEFAULT 'CLIENT',
    company_id INTEGER REFERENCES companies(id), -- Chave estrangeira para a empresa à qual o usuário pertence
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Agora que a tabela 'users' existe, podemos adicionar a chave estrangeira em 'companies'
ALTER TABLE companies
ADD CONSTRAINT fk_admin_user
FOREIGN KEY (admin_user_id)
REFERENCES users(id);

-- Cria uma função de gatilho (trigger) para atualizar automaticamente o campo 'updated_at'
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplica o gatilho à tabela 'users'
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Aplica o gatilho à tabela 'companies'
CREATE TRIGGER update_companies_updated_at
BEFORE UPDATE ON companies
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- CORREÇÃO: Comandos de verificação substituídos por SQL padrão
-- Comandos para verificar se as tabelas foram criadas corretamente
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Para ver a estrutura detalhada de cada tabela
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users';

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'companies';