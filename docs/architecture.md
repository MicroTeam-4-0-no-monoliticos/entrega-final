# Arquitectura del Microservicio de Pagos

## Diagrama de Arquitectura Hexagonal

```mermaid
graph TB
    subgraph "Capa de Presentación"
        API[FastAPI Endpoints]
        SWAGGER[Swagger UI]
    end
    
    subgraph "Capa de Aplicación"
        CMD[Comandos]
        QRY[Queries]
        HANDLER[Handlers]
    end
    
    subgraph "Capa de Dominio"
        AGG[Agregado Pago]
        EVT[Eventos de Dominio]
        REGLAS[Reglas de Negocio]
        PUERTO[Puerto PasarelaDePagos]
    end
    
    subgraph "Capa de Infraestructura"
        REPO[Repositorio SQLAlchemy]
        ADAPTER[Stripe Adapter]
        OUTBOX[Pulsar Outbox Processor]
        DB[(PostgreSQL)]
        PULSAR[Apache Pulsar]
        CONSUMER[Pulsar Consumer]
    end
    
    API --> CMD
    API --> QRY
    CMD --> HANDLER
    QRY --> HANDLER
    HANDLER --> AGG
    HANDLER --> REPO
    AGG --> PUERTO
    AGG --> EVT
    PUERTO --> ADAPTER
    REPO --> DB
    REPO --> OUTBOX
    OUTBOX --> PULSAR
    PULSAR --> CONSUMER
    
    style AGG fill:#e1f5fe
    style EVT fill:#f3e5f5
    style PUERTO fill:#fff3e0
    style ADAPTER fill:#e8f5e8
    style PULSAR fill:#ffebee
    style CONSUMER fill:#f1f8e9
```

## Flujo de Procesamiento de Pagos

```mermaid
sequenceDiagram
    participant Client as Cliente
    participant API as API Endpoint
    participant Handler as Command Handler
    participant Pago as Agregado Pago
    participant Pasarela as Pasarela de Pagos
    participant Repo as Repositorio
    participant Outbox as Outbox
    participant Processor as Pulsar Outbox Processor
    participant Pulsar as Apache Pulsar
    participant Consumer as Pulsar Consumer

    Client->>API: POST /pagos/
    API->>Handler: ProcesarPagoCommand
    Handler->>Pago: Crear agregado
    Handler->>Pago: procesar(pasarela)
    Pago->>Pasarela: procesar_pago()
    Pasarela-->>Pago: ResultadoPago
    Pago->>Pago: Actualizar estado
    Pago->>Pago: Agregar evento
    Handler->>Repo: agregar(pago)
    Repo->>Outbox: Guardar eventos
    Repo-->>Handler: Confirmación
    Handler-->>API: Respuesta
    API-->>Client: JSON Response
    
    Note over Processor: Procesamiento Asíncrono
    Processor->>Outbox: Leer eventos pendientes
    Outbox-->>Processor: Eventos
    Processor->>Pulsar: Publicar eventos
    Pulsar-->>Consumer: Entregar eventos
    Consumer->>Consumer: Procesar eventos
    Processor->>Outbox: Marcar como procesados
```

## Patrón Outbox con Apache Pulsar

```mermaid
graph LR
    subgraph "Transacción de Base de Datos"
        A[Actualizar Pago] --> B[Insertar Evento en Outbox]
        B --> C[Commit Transacción]
    end
    
    subgraph "Procesamiento Asíncrono"
        D[Pulsar Outbox Processor] --> E[Leer Eventos Pendientes]
        E --> F[Publicar a Apache Pulsar]
        F --> G[Marcar como Procesados]
    end
    
    subgraph "Consumo de Eventos"
        H[Pulsar Consumer] --> I[Procesar Eventos]
        I --> J[Ejecutar Lógica de Negocio]
    end
    
    C --> D
    F --> H
    
    style A fill:#e3f2fd
    style B fill:#e8f5e8
    style C fill:#fff3e0
    style D fill:#f3e5f5
    style F fill:#ffebee
    style H fill:#f1f8e9
```

## Estados del Agregado Pago

```mermaid
stateDiagram-v2
    [*] --> PENDIENTE: Crear pago
    PENDIENTE --> PROCESANDO: procesar()
    PROCESANDO --> EXITOSO: Pasarela exitosa
    PROCESANDO --> FALLIDO: Pasarela fallida
    EXITOSO --> [*]
    FALLIDO --> [*]
    
    note right of PENDIENTE: Estado inicial del pago
    note right of PROCESANDO: Comunicándose con pasarela
    note right of EXITOSO: Pago completado exitosamente
    note right of FALLIDO: Pago falló, contiene mensaje de error
```

## Componentes del Sistema

### Capa de Dominio
- **Agregado Pago**: Entidad principal que encapsula la lógica de negocio
- **Eventos de Dominio**: PagoExitoso, PagoFallido
- **Reglas de Negocio**: Validaciones de estado y transiciones
- **Puerto PasarelaDePagos**: Interfaz abstracta para pasarelas externas

### Capa de Aplicación
- **Comandos**: ProcesarPagoCommand
- **Queries**: ObtenerEstadoPagoQuery
- **Handlers**: Lógica de orquestación entre dominio e infraestructura

### Capa de Infraestructura
- **Repositorio**: Persistencia con SQLAlchemy
- **Adaptador Stripe**: Implementación mock de la pasarela
- **Pulsar Outbox Processor**: Procesamiento asíncrono de eventos con Pulsar
- **Pulsar Event Consumer**: Consumidor de eventos de Pulsar
- **Base de Datos**: PostgreSQL con tablas pagos y outbox
- **Apache Pulsar**: Sistema de mensajería distribuida

### Capa de Presentación
- **FastAPI**: Endpoints REST con documentación automática
- **Swagger UI**: Interfaz de documentación interactiva
