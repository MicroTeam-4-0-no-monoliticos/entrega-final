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

-- Tablas para el módulo de Reporting
-- Tabla de reportes
CREATE TABLE IF NOT EXISTS reportes (
    id VARCHAR(255) PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    fecha_generacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datos TEXT NOT NULL,
    metadatos TEXT NOT NULL,
    version_servicio_datos VARCHAR(50) NOT NULL
);

-- Índices para la tabla de reportes
CREATE INDEX IF NOT EXISTS idx_reportes_tipo ON reportes(tipo);
CREATE INDEX IF NOT EXISTS idx_reportes_fecha_generacion ON reportes(fecha_generacion);
CREATE INDEX IF NOT EXISTS idx_reportes_version_servicio ON reportes(version_servicio_datos);

-- Tabla de configuración del servicio de datos
CREATE TABLE IF NOT EXISTS configuracion_servicio_datos (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    version VARCHAR(50) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices para la tabla de configuración
CREATE INDEX IF NOT EXISTS idx_config_activo ON configuracion_servicio_datos(activo);
CREATE INDEX IF NOT EXISTS idx_config_fecha_actualizacion ON configuracion_servicio_datos(fecha_actualizacion);

-- Insertar configuración inicial del servicio de datos v1 (usando servicio principal)
INSERT INTO configuracion_servicio_datos (url, version, activo, fecha_actualizacion)
VALUES ('http://aeropartners-app:8000', 'v1', true, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Comentarios sobre los servicios de datos mock
-- Los servicios de datos v1 y v2 están configurados en docker-compose.yml
-- v1: http://servicio-datos-v1:8000 (puerto externo 9001)
-- v2: http://servicio-datos-v2:8000 (puerto externo 9002)
-- El servicio de reporting puede cambiar entre versiones sin interrupción
