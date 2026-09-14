CREATE DATABASE IF NOT EXISTS roger_partidaco;
USE roger_partidaco;

DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS objetos_do_roger;

CREATE TABLE objetos_do_roger (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(50) NOT NULL,
    qtd INT NOT NULL,
    preco DECIMAL(10, 2) NOT NULL,
    imagem VARCHAR(500) NOT NULL
);

INSERT INTO objetos_do_roger (nome, descricao, qtd, preco, imagem)
VALUES ('chave de fenda', 'serve para apertar', 78, 67.00, 'static/chavedefenda.png');

CREATE TABLE usuarios (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    tipo VARCHAR(255) 
);

-- MODIFICADO: o usuario inicial pode acessar a area administrativa.
INSERT INTO usuarios (nome, senha, tipo)
VALUES ('antonio', '$2b$12$XVbddUga1J3cQ14.y7q0qeZV88.gj/22fRv.wn7wePBvVM331ljJ6', 'admin');

SELECT * FROM objetos_do_roger;
SELECT * FROM usuarios;