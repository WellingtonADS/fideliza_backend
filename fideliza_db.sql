-- 1. Cria a tabela 'companies'
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    admin_user_id INTEGER, -- Chave estrangeira será adicionada depois
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 2. Cria a tabela 'users'
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    qr_code_base64 TEXT,
    user_type VARCHAR(50) NOT NULL DEFAULT 'CLIENT',
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 3. Adiciona a chave estrangeira que faltava em 'companies'
ALTER TABLE companies
ADD CONSTRAINT fk_admin_user
FOREIGN KEY (admin_user_id)
REFERENCES users(id);

-- 4. Cria a nova tabela 'point_transactions'
CREATE TABLE point_transactions (
    id SERIAL PRIMARY KEY,
    points INTEGER NOT NULL DEFAULT 1,
    client_id INTEGER NOT NULL REFERENCES users(id),
    company_id INTEGER NOT NULL REFERENCES companies(id),
    awarded_by_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 5. Cria a função de gatilho (trigger) para atualizar 'updated_at'
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

-- 6. Aplica o gatilho às tabelas
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at
BEFORE UPDATE ON companies
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 7. Concede as permissões necessárias para o utilizador da aplicação
GRANT ALL PRIVILEGES ON TABLE users, companies, point_transactions TO fideliza_user;
GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO fideliza_user;
GRANT USAGE, SELECT ON SEQUENCE companies_id_seq TO fideliza_user;
GRANT USAGE, SELECT ON SEQUENCE point_transactions_id_seq TO fideliza_user;
