"""
Modelos de base de datos para el módulo de Reporting
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from ..dominio.objetos_valor import TipoReporte

Base = declarative_base()


class ReporteModel(Base):
    """Modelo de base de datos para reportes"""
    __tablename__ = "reportes"
    
    id = Column(String(255), primary_key=True, index=True)
    tipo = Column(Enum(TipoReporte), nullable=False, index=True)
    fecha_generacion = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    datos = Column(Text, nullable=False)  # JSON como texto
    metadatos = Column(Text, nullable=False)  # JSON como texto
    version_servicio_datos = Column(String(50), nullable=False)
    
    def __repr__(self):
        return f"<ReporteModel(id='{self.id}', tipo='{self.tipo}')>"


class ConfiguracionServicioDatosModel(Base):
    """Modelo de base de datos para configuración del servicio de datos"""
    __tablename__ = "configuracion_servicio_datos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), nullable=False)
    version = Column(String(50), nullable=False)
    activo = Column(Boolean, default=True, nullable=False, index=True)
    fecha_actualizacion = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ConfiguracionServicioDatosModel(url='{self.url}', version='{self.version}', activo={self.activo})>"
