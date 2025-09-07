#!/bin/bash

# Script de inicio rápido para el Microservicio de Pagos de Aeropartners

echo "🚀 Iniciando Microservicio de Pagos - Aeropartners"
echo "=================================================="

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

# Verificar que Docker Compose esté instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor instala Docker Compose primero."
    exit 1
fi

# Detener contenedores existentes si los hay
echo "🛑 Deteniendo contenedores existentes..."
docker-compose down

# Construir y levantar los servicios
echo "🔨 Construyendo y levantando servicios..."
docker-compose up -d --build

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 15

# Verificar el estado de los servicios
echo "📊 Estado de los servicios:"
docker-compose ps

# Verificar que la API esté respondiendo
echo "🔍 Verificando que la API esté funcionando..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API funcionando correctamente"
else
    echo "❌ API no está respondiendo. Revisa los logs con: docker-compose logs aeropartners"
fi

echo ""
echo "🎉 ¡Microservicio de Pagos con Apache Pulsar iniciado exitosamente!"
echo ""
echo "📋 Información útil:"
echo "   • API: http://localhost:8000"
echo "   • Swagger UI: http://localhost:8000/docs"
echo "   • ReDoc: http://localhost:8000/redoc"
echo "   • Health Check: http://localhost:8000/health"
echo "   • Pulsar Admin: http://localhost:8080"
echo "   • Pulsar Topic Stats: http://localhost:8080/admin/v2/persistent/public/default/pagos-events/stats"
echo ""
echo "🧪 Para probar la API, ejecuta:"
echo "   python scripts/test_api.py"
echo ""
echo "📝 Para ver los logs:"
echo "   docker-compose logs -f aeropartners"
echo "   docker-compose logs -f outbox-processor"
echo "   docker-compose logs -f pulsar-consumer"
echo ""
echo "🛑 Para detener los servicios:"
echo "   docker-compose down"
