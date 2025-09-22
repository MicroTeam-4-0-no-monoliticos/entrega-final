"""
Repositorios de infraestructura para el módulo de Reporting
"""
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..dominio.entidades import Reporte, ConfiguracionServicioDatos
from ..dominio.repositorios import ReporteRepository, ConfiguracionServicioDatosRepository
from ..dominio.objetos_valor import FiltrosReporte

logger = logging.getLogger(__name__)


class ReporteRepositoryImpl(ReporteRepository):
    """Implementación del repositorio de reportes usando PostgreSQL"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _create_session(self):
        """Crea una nueva sesión de base de datos"""
        return self.SessionLocal()
    
    def guardar(self, reporte: Reporte) -> None:
        """Guarda un reporte en la base de datos"""
        try:
            with self._create_session() as session:
                # Convertir entidad a diccionario para insertar
                reporte_data = {
                    'id': reporte.id,
                    'tipo': reporte.tipo,
                    'fecha_generacion': reporte.fecha_generacion,
                    'datos': json.dumps(reporte.datos),
                    'metadatos': json.dumps(reporte.metadatos),
                    'version_servicio_datos': reporte.version_servicio_datos
                }
                
                # Insertar usando SQL directo
                insert_query = text("""
                    INSERT INTO reportes (id, tipo, fecha_generacion, datos, metadatos, version_servicio_datos)
                    VALUES (:id, :tipo, :fecha_generacion, :datos, :metadatos, :version_servicio_datos)
                    ON CONFLICT (id) DO UPDATE SET
                        tipo = EXCLUDED.tipo,
                        fecha_generacion = EXCLUDED.fecha_generacion,
                        datos = EXCLUDED.datos,
                        metadatos = EXCLUDED.metadatos,
                        version_servicio_datos = EXCLUDED.version_servicio_datos
                """)
                
                session.execute(insert_query, reporte_data)
                session.commit()
                logger.info(f"Reporte guardado: {reporte.id}")
                
        except Exception as e:
            logger.error(f"Error guardando reporte {reporte.id}: {str(e)}")
            raise
    
    def obtener_por_id(self, reporte_id: str) -> Optional[Reporte]:
        """Obtiene un reporte por su ID"""
        try:
            with self._create_session() as session:
                query = text("""
                    SELECT id, tipo, fecha_generacion, datos, metadatos, version_servicio_datos
                    FROM reportes
                    WHERE id = :reporte_id
                """)
                
                result = session.execute(query, {"reporte_id": reporte_id}).fetchone()
                
                if result:
                    return self._row_to_reporte(result)
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo reporte {reporte_id}: {str(e)}")
            raise
    
    def obtener_por_tipo(self, tipo: str, filtros: Optional[FiltrosReporte] = None) -> List[Reporte]:
        """Obtiene reportes por tipo con filtros opcionales"""
        try:
            with self._create_session() as session:
                query = text("""
                    SELECT id, tipo, fecha_generacion, datos, metadatos, version_servicio_datos
                    FROM reportes
                    WHERE tipo = :tipo
                    ORDER BY fecha_generacion DESC
                    LIMIT 50
                """)
                
                results = session.execute(query, {"tipo": tipo}).fetchall()
                
                reportes = [self._row_to_reporte(row) for row in results]
                
                # Aplicar filtros adicionales si se proporcionan
                if filtros and filtros.periodo:
                    reportes = [
                        r for r in reportes 
                        if filtros.periodo.incluye_fecha(r.fecha_generacion.date())
                    ]
                
                return reportes
                
        except Exception as e:
            logger.error(f"Error obteniendo reportes por tipo {tipo}: {str(e)}")
            raise
    
    def obtener_recientes(self, limite: int = 10) -> List[Reporte]:
        """Obtiene los reportes más recientes"""
        try:
            with self._create_session() as session:
                query = text("""
                    SELECT id, tipo, fecha_generacion, datos, metadatos, version_servicio_datos
                    FROM reportes
                    ORDER BY fecha_generacion DESC
                    LIMIT :limite
                """)
                
                results = session.execute(query, {"limite": limite}).fetchall()
                return [self._row_to_reporte(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error obteniendo reportes recientes: {str(e)}")
            raise
    
    def eliminar_antiguos(self, dias_antiguedad: int) -> int:
        """Elimina reportes más antiguos que el número de días especificado"""
        try:
            with self._create_session() as session:
                fecha_limite = datetime.utcnow() - timedelta(days=dias_antiguedad)
                
                query = text("""
                    DELETE FROM reportes
                    WHERE fecha_generacion < :fecha_limite
                """)
                
                result = session.execute(query, {"fecha_limite": fecha_limite})
                session.commit()
                
                eliminados = result.rowcount
                logger.info(f"Eliminados {eliminados} reportes antiguos")
                return eliminados
                
        except Exception as e:
            logger.error(f"Error eliminando reportes antiguos: {str(e)}")
            raise
    
    def _row_to_reporte(self, row) -> Reporte:
        """Convierte una fila de la base de datos a una entidad Reporte"""
        from ..dominio.entidades import TipoReporte
        
        return Reporte(
            id=row.id,
            tipo=TipoReporte(row.tipo),
            fecha_generacion=row.fecha_generacion,
            datos=json.loads(row.datos),
            metadatos=json.loads(row.metadatos),
            version_servicio_datos=row.version_servicio_datos
        )


class ConfiguracionServicioDatosRepositoryImpl(ConfiguracionServicioDatosRepository):
    """Implementación del repositorio de configuración usando PostgreSQL"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _create_session(self):
        """Crea una nueva sesión de base de datos"""
        return self.SessionLocal()
    
    def obtener_configuracion_activa(self) -> Optional[ConfiguracionServicioDatos]:
        """Obtiene la configuración activa del servicio de datos"""
        try:
            with self._create_session() as session:
                query = text("""
                    SELECT url, version, activo, updated_at
                    FROM configuracion_servicio_datos
                    WHERE activo = true
                    ORDER BY updated_at DESC
                    LIMIT 1
                """)
                
                result = session.execute(query).fetchone()
                
                if result:
                    return ConfiguracionServicioDatos(
                        url=result.url,
                        version=result.version,
                        activo=result.activo,
                        fecha_actualizacion=result.updated_at
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo configuración activa: {str(e)}")
            raise
    
    def guardar_configuracion(self, configuracion: ConfiguracionServicioDatos) -> None:
        """Guarda la configuración del servicio de datos"""
        try:
            with self._create_session() as session:
                config_data = {
                    'url': configuracion.url,
                    'version': configuracion.version,
                    'activo': configuracion.activo,
                    'fecha_actualizacion': configuracion.fecha_actualizacion
                }
                
                insert_query = text("""
                    INSERT INTO configuracion_servicio_datos (url, version, activo, fecha_actualizacion)
                    VALUES (:url, :version, :activo, :fecha_actualizacion)
                """)
                
                session.execute(insert_query, config_data)
                session.commit()
                logger.info(f"Configuración guardada: {configuracion.url} (v{configuracion.version})")
                
        except Exception as e:
            logger.error(f"Error guardando configuración: {str(e)}")
            raise
    
    def obtener_historial_configuraciones(self) -> List[ConfiguracionServicioDatos]:
        """Obtiene el historial de configuraciones"""
        try:
            with self._create_session() as session:
                query = text("""
                    SELECT url, version, activo, updated_at
                    FROM configuracion_servicio_datos
                    ORDER BY updated_at DESC
                """)
                
                results = session.execute(query).fetchall()
                
                return [
                    ConfiguracionServicioDatos(
                        url=row.url,
                        version=row.version,
                        activo=row.activo,
                        fecha_actualizacion=row.updated_at
                    )
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error obteniendo historial de configuraciones: {str(e)}")
            raise
    
    def desactivar_configuracion_actual(self) -> None:
        """Desactiva la configuración actual"""
        try:
            with self._create_session() as session:
                query = text("""
                    UPDATE configuracion_servicio_datos
                    SET activo = false
                    WHERE activo = true
                """)
                
                session.execute(query)
                session.commit()
                logger.info("Configuración actual desactivada")
                
        except Exception as e:
            logger.error(f"Error desactivando configuración actual: {str(e)}")
            raise
