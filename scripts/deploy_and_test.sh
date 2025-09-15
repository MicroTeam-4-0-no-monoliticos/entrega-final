#!/bin/bash

# Script de despliegue y prueba completo para Aeropartners
# Incluye todos los servicios: Pagos, Campañas y Reporting

set -e

echo "🚀 Aeropartners - Despliegue Completo con Docker"
echo "================================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que Docker esté ejecutándose
print_status "Verificando Docker..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker no está ejecutándose. Por favor inicia Docker Desktop o Colima."
    exit 1
fi
print_success "Docker está ejecutándose"

# Verificar que estemos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    print_error "No se encontró docker-compose.yml. Ejecuta este script desde el directorio entrega-final"
    exit 1
fi

# Limpiar contenedores existentes
print_status "Limpiando contenedores existentes..."
docker-compose down -v 2>/dev/null || true
print_success "Contenedores limpiados"

# Construir y levantar todos los servicios
print_status "Construyendo y levantando todos los servicios..."
print_status "Esto puede tomar varios minutos la primera vez..."

docker-compose up -d --build

# Esperar a que los servicios estén listos
print_status "Esperando a que los servicios estén listos..."
sleep 30

# Verificar estado de los servicios
print_status "Verificando estado de los servicios..."
docker-compose ps

# Verificar que los servicios estén saludables
print_status "Verificando salud de los servicios..."

# Función para verificar endpoint
check_endpoint() {
    local url=$1
    local service_name=$2
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_success "$service_name está respondiendo en $url"
            return 0
        fi
        print_status "Intento $attempt/$max_attempts: Esperando $service_name..."
        sleep 5
        ((attempt++))
    done
    
    print_error "$service_name no está respondiendo después de $max_attempts intentos"
    return 1
}

# Verificar servicios principales
check_endpoint "http://localhost:8000/health" "Aeropartners Principal"
check_endpoint "http://localhost:8001/health" "Campañas Primario"
check_endpoint "http://localhost:8002/health" "Campañas Réplica"
check_endpoint "http://localhost:8080/health" "Proxy de Campañas"
check_endpoint "http://localhost:9001/health" "Servicio de Datos v1"
check_endpoint "http://localhost:9002/health" "Servicio de Datos v2"

# Verificar servicio de reporting
check_endpoint "http://localhost:8000/reporting/health" "Servicio de Reporting"

print_success "Todos los servicios están funcionando correctamente!"

# Mostrar información de acceso
echo ""
echo "📋 Información de Acceso:"
echo "========================"
echo "🌐 Servicios Web:"
echo "   • Aeropartners Principal: http://localhost:8000"
echo "   • Campañas Primario: http://localhost:8001"
echo "   • Campañas Réplica: http://localhost:8002"
echo "   • Proxy de Campañas: http://localhost:8080"
echo "   • Servicio de Datos v1: http://localhost:9001"
echo "   • Servicio de Datos v2: http://localhost:9002"
echo ""
echo "📊 Servicio de Reporting:"
echo "   • Generar reporte: POST http://localhost:8000/reporting/report"
echo "   • Cambiar servicio: POST http://localhost:8000/reporting/admin/servicio-datos"
echo "   • Ver configuración: GET http://localhost:8000/reporting/admin/configuracion"
echo "   • Health check: GET http://localhost:8000/reporting/health"
echo ""
echo "🗄️ Base de Datos:"
echo "   • PostgreSQL: localhost:5432"
echo "   • Usuario: postgres"
echo "   • Contraseña: postgres"
echo "   • Base de datos: aeropartners"
echo ""
echo "📨 Apache Pulsar:"
echo "   • Service URL: pulsar://localhost:6650"
echo "   • Admin URL: http://localhost:8081"
echo ""

# Ejecutar pruebas del servicio de reporting
print_status "Ejecutando pruebas del servicio de reporting..."
if [ -f "scripts/test_reporting.py" ]; then
    python scripts/test_reporting.py
    print_success "Pruebas del servicio de reporting completadas"
else
    print_warning "Script de pruebas no encontrado, saltando pruebas automáticas"
fi

# Mostrar comandos útiles
echo ""
echo "🔧 Comandos Útiles:"
echo "==================="
echo "• Ver logs de todos los servicios:"
echo "  docker-compose logs -f"
echo ""
echo "• Ver logs de un servicio específico:"
echo "  docker-compose logs -f aeropartners"
echo "  docker-compose logs -f campaigns-svc"
echo "  docker-compose logs -f servicio-datos-v1"
echo ""
echo "• Detener todos los servicios:"
echo "  docker-compose down"
echo ""
echo "• Reiniciar un servicio específico:"
echo "  docker-compose restart aeropartners"
echo ""
echo "• Acceder a la base de datos:"
echo "  docker exec -it aeropartners-postgres psql -U postgres -d aeropartners"
echo ""

# Mostrar ejemplos de uso
echo "📝 Ejemplos de Uso del Servicio de Reporting:"
echo "============================================="
echo ""
echo "1. Generar reporte de pagos:"
echo "curl -X POST 'http://localhost:8000/reporting/report' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"tipo_reporte\": \"pagos_por_periodo\", \"filtros\": {\"fecha_inicio\": \"2024-01-01\", \"fecha_fin\": \"2024-01-31\"}}'"
echo ""
echo "2. Cambiar a servicio v2:"
echo "curl -X POST 'http://localhost:8000/reporting/admin/servicio-datos' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"url\": \"http://servicio-datos-v2:8000\", \"version\": \"v2\"}'"
echo ""
echo "3. Ver configuración actual:"
echo "curl 'http://localhost:8000/reporting/admin/configuracion'"
echo ""

print_success "¡Despliegue completado exitosamente!"
print_status "Todos los servicios están ejecutándose y listos para usar"
print_warning "Para detener los servicios, ejecuta: docker-compose down"
