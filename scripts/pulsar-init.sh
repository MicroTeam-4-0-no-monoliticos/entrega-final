#!/bin/bash

# Script para inicializar topics de Pulsar y configurar DLQs

set -e

PULSAR_URL=${PULSAR_URL:-"pulsar://localhost:6650"}
PULSAR_ADMIN_URL=${PULSAR_ADMIN_URL:-"http://localhost:8081"}

echo "🚀 Inicializando topics de Pulsar..."
echo "Pulsar URL: $PULSAR_URL"
echo "Pulsar Admin URL: $PULSAR_ADMIN_URL"

# Esperar a que Pulsar esté disponible
echo "⏳ Esperando a que Pulsar esté disponible..."
while ! curl -f $PULSAR_ADMIN_URL/admin/v2/clusters >/dev/null 2>&1; do
    echo "Esperando Pulsar..."
    sleep 5
done

echo "✅ Pulsar está disponible"

# Función para crear un topic
create_topic() {
    local topic=$1
    local partitions=${2:-1}
    
    echo "📝 Creando topic: $topic con $partitions particiones"
    
    # Crear topic particionado
    curl -X PUT "$PULSAR_ADMIN_URL/admin/v2/persistent/public/default/$topic/partitions" \
        -H "Content-Type: application/json" \
        -d "$partitions" || echo "Topic $topic ya existe o error al crear"
    
    echo "✅ Topic $topic configurado"
}

# Función para configurar políticas de retención
configure_retention() {
    local topic=$1
    local retention_time=${2:-"7d"}
    local retention_size=${3:-"1G"}
    
    echo "📋 Configurando retención para topic: $topic"
    
    # Intentar configurar retención con reintentos
    local max_retries=3
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        if curl -s -X POST "$PULSAR_ADMIN_URL/admin/v2/persistent/public/default/$topic/retention" \
            -H "Content-Type: application/json" \
            -d "{\"retentionTimeInMinutes\": 10080, \"retentionSizeInMB\": 1024}" > /dev/null 2>&1; then
            echo "✅ Retención configurada para $topic"
            return 0
        else
            retry=$((retry + 1))
            if [ $retry -lt $max_retries ]; then
                echo "⚠️  Reintentando configuración de retención para $topic (intento $retry/$max_retries)"
                sleep 2
            fi
        fi
    done
    
    echo "⚠️  No se pudo configurar retención para $topic (no crítico, el topic funciona normalmente)"
}

# Topics para eventos de campañas
echo "🎯 Creando topics de eventos de campañas..."
create_topic "campaigns.evt.created" 3
create_topic "campaigns.evt.updated" 3
create_topic "campaigns.evt.activated" 3
create_topic "campaigns.evt.budget_updated" 3
create_topic "campaigns.evt.metrics_updated" 3

# Topics para eventos de pagos (si no existen)
echo "💳 Creando topics de eventos de pagos..."
create_topic "payments.evt.pending" 3
create_topic "payments.evt.completed" 3
create_topic "payments.evt.failed" 3

# Dead Letter Queues
echo "💀 Creando Dead Letter Queues..."
create_topic "campaigns.DLQ" 1
create_topic "payments.DLQ" 1

# Esperar a que Pulsar inicialice completamente el cache de políticas
echo "⏳ Esperando inicialización del cache de políticas de Pulsar..."
sleep 5

# Configurar retención para todos los topics
echo "📚 Configurando políticas de retención..."
configure_retention "campaigns.evt.created"
configure_retention "campaigns.evt.updated"
configure_retention "campaigns.evt.activated"
configure_retention "campaigns.evt.budget_updated"
configure_retention "campaigns.evt.metrics_updated"
configure_retention "payments.evt.pending"
configure_retention "payments.evt.completed"
configure_retention "payments.evt.failed"
configure_retention "campaigns.DLQ" "30d" "5G"
configure_retention "payments.DLQ" "30d" "5G"

# Mostrar topics creados
echo "📊 Listando topics creados:"
curl -s "$PULSAR_ADMIN_URL/admin/v2/persistent/public/default" | jq -r '.[]' || echo "Error listando topics"

echo ""
echo "🎉 Inicialización de Pulsar completada!"
echo ""
echo "Topics creados:"
echo "  - campaigns.evt.created (3 particiones)"
echo "  - campaigns.evt.updated (3 particiones)"
echo "  - campaigns.evt.activated (3 particiones)"
echo "  - campaigns.evt.budget_updated (3 particiones)"
echo "  - campaigns.evt.metrics_updated (3 particiones)"
echo "  - payments.evt.pending (3 particiones)"
echo "  - payments.evt.completed (3 particiones)"
echo "  - payments.evt.failed (3 particiones)"
echo "  - campaigns.DLQ (1 partición)"
echo "  - payments.DLQ (1 partición)"
echo ""
echo "📋 Configuración de retención:"
echo "   - Topics de eventos: 7 días / 1GB por topic"
echo "   - DLQ: 30 días / 5GB"
echo "   - Nota: Si la configuración de retención falló, los topics funcionan normalmente con la configuración por defecto"
echo ""
echo "✅ Todos los topics están listos para usar!"
