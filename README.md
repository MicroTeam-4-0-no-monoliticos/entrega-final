# Microservicio de Pagos - Aeropartners

## Descripción del Servicio

Este microservicio implementa el **"Microservicio de Pagos"** para la plataforma "Alpes Partners", siguiendo los principios de **Domain-Driven Design (DDD)** y **Arquitectura Hexagonal**. El servicio está diseñado para manejar el procesamiento de pagos a afiliados con alta concurrencia y consistencia de datos.

### Escenario de Calidad #6: Procesamiento Concurrente de Pagos

El servicio implementa el escenario de procesamiento concurrente de pagos, validando la capacidad del sistema para orquestar un alto volumen de transacciones con una pasarela de pagos externa de manera eficiente y resiliente.

## Arquitectura y Decisiones de Diseño

### 1. Domain-Driven Design (DDD)

**Agregado Principal: `Pago`**
- Modela el ciclo de vida completo del pago con estados: `PENDIENTE`, `PROCESANDO`, `EXITOSO`, `FALLIDO`
- Protege las invariantes de negocio (no se puede procesar un pago ya procesado)
- Contiene la lógica de transición de estados y generación de eventos de dominio

**Objetos de Valor:**
- `Dinero`: Encapsula monto y moneda con validaciones
- `Moneda`: Enum con monedas soportadas (USD, EUR, COP)

**Eventos de Dominio:**
- `PagoExitoso`: Se emite cuando un pago se procesa exitosamente
- `PagoFallido`: Se emite cuando un pago falla con el mensaje de error

### 2. Arquitectura Hexagonal (Puertos y Adaptadores)

**Puerto: `PasarelaDePagos`**
- Define la interfaz abstracta para la comunicación con pasarelas de pago externas
- Permite intercambiar implementaciones sin afectar el dominio

**Adaptador: `StripeAdapter`**
- Implementa el puerto `PasarelaDePagos`
- Simula llamadas HTTP a la API de Stripe con latencia y fallos aleatorios
- Retorna `ResultadoPago` con éxito/fallo y mensajes de error

### 3. Patrón Outbox con Apache Pulsar

**Implementación:**
- Al persistir el agregado `Pago`, los eventos se guardan en la tabla `outbox` en la misma transacción
- Un procesador separado (`PulsarOutboxProcessor`) lee y publica los eventos a Apache Pulsar
- Un consumidor (`PulsarEventConsumer`) procesa los eventos publicados
- Garantiza consistencia entre el estado del pago y la publicación de eventos

**Beneficios:**
- Evita problemas de consistencia eventual
- Permite reintentos en caso de fallos en la publicación
- Mantiene el orden de los eventos
- Escalabilidad horizontal con múltiples consumidores
- Durabilidad y persistencia de mensajes
- Integración con sistemas externos

### 4. CQS (Command Query Separation)

**Comandos:**
- `ProcesarPagoCommand`: Inicia el flujo de procesamiento de pago
- `ProcesarPagoHandler`: Maneja la lógica de negocio del comando

**Consultas:**
- `ObtenerEstadoPagoQuery`: Consulta el estado actual de un pago
- `ObtenerEstadoPagoHandler`: Retorna la información del pago

## Stack Tecnológico

- **Lenguaje:** Python 3.11+
- **Framework:** FastAPI
- **Base de Datos:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
- **Migraciones:** Alembic
- **Broker de eventos:** Apache Pulsar 3.1.0
- **Contenerización:** Docker y Docker Compose

## Estructura del Proyecto

```
src/aeropartners/
├── api/                    # Capa de presentación (FastAPI)
│   └── pagos.py
├── modulos/
│   └── pagos/
│       ├── aplicacion/     # Capa de aplicación (CQS)
│       │   ├── comandos.py
│       │   ├── queries.py
│       │   └── handlers.py
│       ├── dominio/        # Capa de dominio (DDD)
│       │   ├── entidades.py
│       │   ├── eventos.py
│       │   ├── reglas.py
│       │   ├── repositorios.py
│       │   └── servicios.py
│       └── infraestructura/ # Capa de infraestructura
│           ├── adaptadores.py
│           ├── modelos.py
│           ├── mapeadores.py
│           ├── outbox.py
│           └── pulsar_consumer.py
├── seedwork/              # Código reutilizable
│   ├── aplicacion/
│   ├── dominio/
│   └── infraestructura/
│       ├── db.py
│       └── pulsar_producer.py
└── main.py               # Punto de entrada de la aplicación
```

## Guía de Ejecución

Cómo desplegar y probar las APIs del experimento.

### Prerrequisitos

### 1.1. Instalar Docker Desktop 

Descargar de esta URL https://www.docker.com/products/docker-desktop/

### 1.2. Instalar Colima (En caso de no poder instalar Docker Desktop)

> En caso de no tener Homewbrew instalado
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
```bash
# Instalar Colima
brew install colima
```
```bash
# Instalar docker
brew install docker
```


### 2. Iniciar Colima

```bash
# Iniciar Colima
colima start

# Verificar que Docker funciona
docker --version
docker ps
```

## Configuración del Proyecto

### 1. Navegar al directorio del proyecto

```bash
cd entrega-3
```

## Ejecución con Docker Compose

### 1. Levantar todos los servicios

```bash
# Colima debe estar ejecutándose
export PATH="/opt/homebrew/bin:$PATH"

# Levantar todos los servicios
docker-compose up -d --build
```

### 2. Verificar estado de los servicios

```bash
# Ver el estado de todos los contenedores
docker-compose ps
```

Debería ver 5 servicios ejecutándose:
- `aeropartners-app` (API principal)
- `aeropartners-postgres` (Base de datos)
- `aeropartners-pulsar` (Sistema de mensajería)
- `aeropartners-outbox` (Procesador de eventos)
- `aeropartners-consumer` (Consumidor de Pulsar)


### 3. Verificar logs de inicialización

```bash
# Ver logs de la aplicación principal
docker-compose logs aeropartners

# Ver logs del procesador de outbox
docker-compose logs outbox-processor

# Ver logs del consumidor de Pulsar
docker-compose logs pulsar-consumer
```

## Pruebas del experimento

### 1. Preparar entorno de pruebas

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias desde requirements.txt
pip install -r requirements
```

### 2. Ejecutar pruebas

```bash
# Ejecutar todas las pruebas
python tests/test_api.py
```

### 3. Pruebas manuales con Postman

Importar la colección `MicroTeam 4.0 - Entrega 3.postman_collection.json` que se encuentra en este mismo repositorio dentro de Postman. Allí encontrará los endpoints vistos en el video de presentación para realizar pruebas manuales del experimento en cuestión.


## Monitoreo y Verificación

### 1. URLs de monitoreo

- **API Principal**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Pulsar Admin**: http://localhost:8080
- **Estadísticas de Pulsar**: http://localhost:8080/admin/v2/persistent/public/default/pagos-events/stats

### 2. Verificar base de datos

```bash
# Conectar a PostgreSQL
docker exec -it aeropartners-postgres psql -U postgres -d aeropartners

# Ver tablas
\dt

# Ver pagos
SELECT * FROM pagos;

# Ver eventos del outbox
SELECT * FROM outbox;

# Salir
\q
```
