-- Script de inicialización de la base de datos para Aeropartners
-- Este archivo se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL

-- Crear la base de datos si no existe
CREATE DATABASE aeropartners;

-- Conectar a la base de datos
\c aeropartners;

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS public;

-- Configurar permisos
GRANT ALL PRIVILEGES ON DATABASE aeropartners TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
