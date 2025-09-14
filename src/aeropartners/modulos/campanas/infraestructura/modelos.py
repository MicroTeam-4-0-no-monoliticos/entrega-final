from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from ....seedwork.infraestructura.db import Base
import uuid
from datetime import datetime

class CampanaModel(Base):
    __tablename__ = "campanas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False)
    descripcion = Column(Text, nullable=True)
    estado = Column(String(20), nullable=False, default="BORRADOR")
    
    # Presupuesto
    presupuesto_monto = Column(Float, nullable=False)
    presupuesto_moneda = Column(String(3), nullable=False)
    
    # Fechas
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now)
    fecha_actualizacion = Column(DateTime, nullable=False, default=datetime.now)
    
    # Métricas
    impresiones = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    conversiones = Column(Integer, nullable=False, default=0)
    gasto_actual = Column(Float, nullable=False, default=0.0)
    
    # Relaciones
    id_afiliado = Column(String(255), nullable=False)

class EventInboxModel(Base):
    """Modelo para la tabla de eventos procesados (idempotencia)"""
    __tablename__ = "event_inbox_campanas"
    
    event_id = Column(UUID(as_uuid=True), primary_key=True)
    event_type = Column(String(100), nullable=False)
    processed_at = Column(DateTime, nullable=False, default=datetime.now)
    payload = Column(JSON, nullable=True)

class OutboxCampanasModel(Base):
    """Modelo para el outbox de eventos de campañas"""
    __tablename__ = "outbox_campanas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=False)
    processed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    processed_at = Column(DateTime, nullable=True)
    topic = Column(String(100), nullable=False)
