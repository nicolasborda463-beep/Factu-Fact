-- Script de referencia para crear la base de datos en MySQL.
-- Solo es necesario si defines DATABASE_URL para usar MySQL en vez de SQLite
-- (por defecto la app funciona con SQLite y crea las tablas automáticamente).

CREATE DATABASE IF NOT EXISTS factu_fact_db CHARACTER SET utf8mb4;
USE factu_fact_db;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    tipo_cuenta VARCHAR(20) NOT NULL,
    nit VARCHAR(50),
    numero_identificacion VARCHAR(50),
    codigo_recuperacion VARCHAR(6),
    codigo_expira DATETIME
);

CREATE TABLE facturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    numero_factura VARCHAR(30) NOT NULL,
    fecha DATE,
    hora TIME,
    nombre_cliente VARCHAR(120) NOT NULL,
    cedula_cliente VARCHAR(30) NOT NULL,
    empresa VARCHAR(120),
    productos TEXT NOT NULL,
    total FLOAT NOT NULL DEFAULT 0,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE gastos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    monto FLOAT NOT NULL DEFAULT 0,
    fecha DATE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);
