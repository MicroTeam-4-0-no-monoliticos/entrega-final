# Distribución del Equipo - Aeropartners

## Información General del Proyecto

**Nombre del Repositorio:** entrega-final  
**Organización:** MicroTeam-4-0-no-monoliticos  
**Rama Principal:** main  

## Integrantes del Equipo

### Héctor Franco (HectorFranco-MISO / Hector Franco - MISO)
- **Responsabilidades:**

#### Arquitectura y Diseño
- Diseño e implementación de la arquitectura hexagonal del sistema
- Implementación de Domain-Driven Design (DDD) y Event-Driven Architecture
- Configuración de la infraestructura de microservicios

#### Desarrollo de Módulos
- **Módulo de Pagos:** Desarrollo completo del bounded context
  - Implementación de agregados, objetos de valor y eventos de dominio
  - Integración con pasarelas de pago (Stripe adapter)
  - Patrón Outbox para consistencia eventual
- **Módulo de Campañas:** Desarrollo completo del bounded context
  - Gestión de estados de campañas y presupuestos
  - Implementación de failover automático con réplicas
  - Consumer pattern para procesamiento de eventos
- **SAGA Orchestrator:** Implementación completa del patrón SAGA
  - Orquestación de transacciones distribuidas
  - Manejo de compensaciones y rollbacks
  - Estados y flujos de trabajo complejos

#### Infraestructura y DevOps
- Dockerización del proyecto completo
- Configuración de Apache Pulsar como message broker
- Deployment en Google Cloud Platform (GKE)
- Configuración de Kubernetes con múltiples servicios
- Implementación de proxies con balanceadores de carga

#### Frontend y Testing
- Desarrollo del frontend inicial en JavaScript
- Deployment en Firebase Hosting
- Creación de colecciones Postman para testing
- Configuración de pruebas de carga con JMeter

### Juan Sebastián Vargas Quintero

- **Responsabilidades:**

#### Servicios de Reporting
- Desarrollo completo del servicio de reportes
- Implementación de versionado sin downtime (v1/v2)
- Read Model CQRS con proyecciones optimizadas
- Actualización en tiempo real desde eventos de Pulsar

#### Configuración de Base de Datos
- Configuración inicial de PostgreSQL
- Diseño de esquemas de base de datos
- Configuración de conexiones y pools de conexiones

#### Documentación y Collections
- Actualización de documentación del proyecto
- Creación y mantenimiento de colecciones Postman
- Configuración de ambientes de prueba

#### Gestión de Proyecto
- Configuración inicial del repositorio
- Gestión de información del equipo
- Mantenimiento de README y documentación técnica

### Angel Farfan Arcila (agfarar)

- **Responsabilidades:**

#### Backend for Frontend
- Desarrollo completo del módulo Event Collector
- Implementación de funcionalidades de recolección de eventos en tiempo real
- Arquitectura completa del BFF con comandos, queries y handlers
- Tests unitarios e integración para el módulo Event Collector
- Implementación de objetos de valor, entidades y eventos de dominio

#### Documentación Técnica y Diagramas
- Creación de diagramas de secuencia de SAGAs
- Diseño del diagrama de contexto de la aplicación
- Documentación de la arquitectura to-be del sistema
- Diseño del diagrama de arquitectura BFF (Backend for Frontend)
- Creación del diagrama de broker de eventos y flujos de messaging

### María Camila Martínez (CamilaMartinez-MISO / María Camila Martínez)

- **Responsabilidades:**

#### Quality Assurance
- Eliminación de código no utilizado y refactoring
- Actualización de coverage de tests
- Mejora de las colecciones Postman para testing

#### Testing y Validación
- Actualización de tests unitarios e integración
- Configuración de métricas de cobertura
- Validación de endpoints y funcionalidades

#### Mantenimiento de Código
- Limpieza de código legacy
- Optimización de imports y dependencias
- Mejora de la calidad del código base


## Metodología de Trabajo

### Gestión de Branches
- **Rama principal:** main
- **Ramas de desarrollo:** feature/escenario-2, feature/implement-reporting, feature/bff, feature/saga
- **Flujo:** Feature branches con pull requests

### Patrones de Commits
- Commits descriptivos con contexto claro
- Separación por funcionalidades y módulos
- Merge commits para integración de features

### Colaboración
- Pull requests con revisión de código
- Integración continua con testing
- Documentación técnica mantenida por el equipo completo
