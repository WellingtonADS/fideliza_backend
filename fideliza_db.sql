-- Script SQL Completo para o Projeto Fideliza+ (Fim da Fase 2)
-- Este script cria toda a estrutura de base de dados necessária para a aplicação.

-- Apaga as tabelas antigas em ordem para evitar erros de dependência.
-- CUIDADO: Isto apaga todos os dados. Use apenas em desenvolvimento.
-- DROP TABLE IF EXISTS redeemed_rewards;
-- DROP TABLE IF EXISTS rewards;
-- DROP TABLE IF EXISTS point_transactions;
-- DROP TABLE IF EXISTS companies CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;


-- 1. Tabela 'companies'
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    admin_user_id INTEGER, -- Chave estrangeira será adicionada depois
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 2. Tabela 'users'
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

-- 4. Tabela 'point_transactions'
CREATE TABLE point_transactions (
    id SERIAL PRIMARY KEY,
    points INTEGER NOT NULL DEFAULT 1,
    client_id INTEGER NOT NULL REFERENCES users(id),
    company_id INTEGER NOT NULL REFERENCES companies(id),
    awarded_by_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 5. Tabela 'rewards'
CREATE TABLE rewards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    points_required INTEGER NOT NULL,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 6. Tabela 'redeemed_rewards'
CREATE TABLE redeemed_rewards (
    id SERIAL PRIMARY KEY,
    reward_id INTEGER NOT NULL REFERENCES rewards(id),
    client_id INTEGER NOT NULL REFERENCES users(id),
    company_id INTEGER NOT NULL REFERENCES companies(id),
    authorized_by_id INTEGER REFERENCES users(id),
    points_spent INTEGER NOT NULL,
    redeemed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 7. Função de gatilho (trigger) para atualizar 'updated_at'
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

-- 8. Aplica o gatilho às tabelas
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at
BEFORE UPDATE ON companies
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 9. Concede as permissões necessárias para o utilizador da aplicação
-- IMPORTANTE: SUBSTITUA 'seu_usuario_da_app' PELO SEU UTILIZADOR REAL DO FICHEIRO .env
GRANT ALL PRIVILEGES ON TABLE users, companies, point_transactions, rewards, redeemed_rewards TO fideliza_user;
GRANT USAGE, SELECT ON SEQUENCE users_id_seq, companies_id_seq, point_transactions_id_seq, rewards_id_seq, redeemed_rewards_id_seq TO fideliza_user;

