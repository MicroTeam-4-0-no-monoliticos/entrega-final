#!/bin/bash

echo "=== DESPLEGANDO AEROPARTNERS COMPLETO EN GKE ==="

# Aplicar manifiestos en orden
echo "1. Creando namespace..."
kubectl apply -f 01-namespace.yaml

echo "2. Aplicando configuración..."
kubectl apply -f 02-configmap.yaml

echo "3. Aplicando secretos..."
kubectl apply -f 03-secret.yaml

echo "4. Desplegando Pulsar..."
kubectl apply -f 04-pulsar-service.yaml
kubectl apply -f 05-pulsar-deployment.yaml

echo "5. Desplegando servicios principales..."
kubectl apply -f 06-main-service.yaml
kubectl apply -f 07-main-deployment.yaml

echo "6. Desplegando consumers y processors..."
kubectl apply -f 08-consumers-deployment.yaml

echo "7. Desplegando SAGA Orchestrator..."
kubectl apply -f 10-saga-deployment.yaml

echo "8. Desplegando servicios de datos..."
kubectl apply -f 11-servicios-datos-deployment.yaml

echo "9. Configurando Ingress..."
kubectl apply -f 09-ingress.yaml

echo "=== ESPERANDO A QUE LOS PODS ESTÉN LISTOS ==="
echo "Esperando Pulsar..."
kubectl wait --for=condition=ready pod -l app=pulsar -n aeropartners --timeout=300s

echo "Esperando servicios principales..."
kubectl wait --for=condition=ready pod -l app=aeropartners -n aeropartners --timeout=300s

echo "Esperando consumers..."
kubectl wait --for=condition=ready pod -l app=consumers -n aeropartners --timeout=300s

echo "=== ESTADO DEL DESPLIEGUE ==="
echo "--- PODS ---"
kubectl get pods -n aeropartners

echo "--- SERVICES ---"
kubectl get services -n aeropartners

echo "--- INGRESS ---"
kubectl get ingress -n aeropartners

echo "=== OBTENIENDO IP EXTERNA ==="
kubectl get service aeropartners-service -n aeropartners

echo "=== DESPLIEGUE COMPLETADO ==="
echo "Servicios disponibles en los siguientes puertos:"
echo "- Aplicación principal: 8000"
echo "- Campañas primario: 8001"
echo "- Campañas réplica: 8002"
echo "- Proxy campañas: 8080"
echo "- Event Collector: 8090"
echo "- SAGA Orchestrator: 8091"
echo "- Servicio datos v1: 9001"
echo "- Servicio datos v2: 9002"