-- Criação do banco de dados
CREATE DATABASE IF NOT EXISTS ride_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ride_db;

-- Tabela: USUÁRIO
CREATE TABLE IF NOT EXISTS usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(20) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    perfil ENUM('Diretor', 'Gestor', 'Professor') NOT NULL,
    ativo BOOLEAN DEFAULT 1
);

-- Tabela: CATEGORIA DE DOCUMENTO
CREATE TABLE IF NOT EXISTS categoria_documento (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nome_categoria VARCHAR(100) NOT NULL,
    id_usuario INT NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT 1,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

-- Tabela: MODELO DE DOCUMENTO
CREATE TABLE IF NOT EXISTS modelo_documento (
    id_modelo_documento INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(100) NOT NULL,
    descricao TEXT,
    arquivo LONGBLOB,  -- Armazena o conteúdo binário do arquivo Word
    id_categoria INT NOT NULL,
    id_usuario INT NOT NULL,
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT 1,
    FOREIGN KEY (id_categoria) REFERENCES categoria_documento(id_categoria),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

-- Tabela: DOCUMENTO PREENCHIDO
CREATE TABLE IF NOT EXISTS documento_preenchido (
    id_documento_preenchido INT AUTO_INCREMENT PRIMARY KEY,
    id_documento_modelo INT NOT NULL,
    id_usuario INT NOT NULL,
    arquivo LONGBLOB,  -- Armazena o conteúdo binário do documento preenchido
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT 1,
    FOREIGN KEY (id_documento_modelo) REFERENCES modelo_documento(id_modelo_documento),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

-- Inserção do usuário master (diretor)
INSERT INTO usuario (nome, cpf, senha, perfil, ativo) VALUES (
    'Administrador',
    '123.456.789-00',
    SHA2('master_2025', 256),
    'Diretor',
    1
);