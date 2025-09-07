-- Script de inicialización de la base de datos
-- Este script se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL

-- Crear la base de datos si no existe
SELECT 'CREATE DATABASE aeropartners'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'aeropartners')\gexec

-- Conectar a la base de datos aeropartners
\c aeropartners;

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Las tablas se crearán automáticamente a través de las migraciones de Alembic
