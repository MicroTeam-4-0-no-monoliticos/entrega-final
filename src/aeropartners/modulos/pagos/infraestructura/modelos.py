"""Modelos de base de datos para el módulo de pagos"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from ....seedwork.infraestructura.db import Base
import uuid
from datetime import datetime

class PagoModel(Base):
    __tablename__ = "pagos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_afiliado = Column(String(255), nullable=False)
    monto = Column(Float, nullable=False)
    moneda = Column(String(3), nullable=False)
    estado = Column(String(20), nullable=False, default="PENDIENTE")
    referencia_pago = Column(String(255), nullable=False, unique=True)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now)
    fecha_actualizacion = Column(DateTime, nullable=False, default=datetime.now)
    fecha_procesamiento = Column(DateTime, nullable=True)
    mensaje_error = Column(Text, nullable=True)

class OutboxModel(Base):
    __tablename__ = "outbox"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_evento = Column(String(100), nullable=False)
    datos_evento = Column(Text, nullable=False)
    procesado = Column(Boolean, nullable=False, default=False)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now)
    fecha_procesamiento = Column(DateTime, nullable=True)
