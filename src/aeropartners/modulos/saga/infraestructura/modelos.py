from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class SagaLogModel(Base):
    """Modelo para el log de SAGAs en PostgreSQL"""
    __tablename__ = "saga_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo = Column(String(100), nullable=False)
    estado = Column(String(50), nullable=False)
    pasos = Column(JSON, nullable=True)  # Lista de pasos ejecutados
    compensaciones = Column(JSON, nullable=True)  # Lista de compensaciones
    datos_iniciales = Column(JSON, nullable=True)  # Datos iniciales de la SAGA
    fecha_inicio = Column(DateTime, nullable=False, default=datetime.now)
    fecha_fin = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    timeout_minutos = Column(String(10), nullable=True, default="30")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

class SagaPasoModel(Base):
    """Modelo para los pasos individuales de una SAGA"""
    __tablename__ = "saga_pasos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    saga_id = Column(UUID(as_uuid=True), nullable=False)
    tipo_paso = Column(String(100), nullable=False)
    datos = Column(JSON, nullable=True)
    resultado = Column(JSON, nullable=True)
    compensacion = Column(JSON, nullable=True)
    exitoso = Column(Boolean, nullable=False, default=False)
    error = Column(Text, nullable=True)
    fecha_ejecucion = Column(DateTime, nullable=False, default=datetime.now)
    fecha_fin = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

class SagaCompensacionModel(Base):
    """Modelo para las compensaciones de una SAGA"""
    __tablename__ = "saga_compensaciones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    saga_id = Column(UUID(as_uuid=True), nullable=False)
    paso_id = Column(UUID(as_uuid=True), nullable=False)  # ID del paso que se compensa
    tipo_compensacion = Column(String(100), nullable=False)
    datos = Column(JSON, nullable=True)
    resultado = Column(JSON, nullable=True)
    exitoso = Column(Boolean, nullable=False, default=False)
    error = Column(Text, nullable=True)
    fecha_ejecucion = Column(DateTime, nullable=False, default=datetime.now)
    fecha_fin = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

class SagaEventModel(Base):
    """Modelo para los eventos de SAGA publicados a Pulsar"""
    __tablename__ = "saga_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    saga_id = Column(UUID(as_uuid=True), nullable=False)
    evento_tipo = Column(String(100), nullable=False)
    evento_datos = Column(JSON, nullable=False)
    topic = Column(String(200), nullable=False, default="saga-events")
    procesado = Column(Boolean, nullable=False, default=False)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now)
    fecha_procesamiento = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    reintentos = Column(String(10), nullable=False, default="0")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
