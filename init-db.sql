-- Script de inicialización de la base de datos para Aeropartners
-- Este archivo se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL

-- Nota: PostgreSQL en Docker crea automáticamente la base de datos especificada en POSTGRES_DB
-- Por lo tanto, no necesitamos crear la base de datos manualmente

-- Conectar a la base de datos aeropartners
\c aeropartners;

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Crear esquema si no existe (aunque 'public' ya existe por defecto)
CREATE SCHEMA IF NOT EXISTS public;

-- Configurar permisos
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
