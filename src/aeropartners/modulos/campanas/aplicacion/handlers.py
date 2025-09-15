from typing import List, Dict, Any
from decimal import Decimal
from ....seedwork.aplicacion.comandos import ComandoHandler
from ....seedwork.aplicacion.queries import QueryHandler, QueryResultado
from ....seedwork.dominio.objetos_valor import Moneda
from ..dominio.entidades import Campana
from ..dominio.enums import TipoCampana
from ..dominio.objetos_valor import Presupuesto
from ..dominio.repositorios import RepositorioCampanas
from ..dominio.servicios import ServicioMetricasImpl, ServicioOptimizacionImpl
from .comandos import (
    CrearCampanaCommand, ActualizarPresupuestoCampanaCommand, ActivarCampanaCommand,
    ActualizarInformacionCampanaCommand, ActualizarMetricasCampanaCommand,
    PausarCampanaCommand, FinalizarCampanaCommand, CancelarCampanaCommand
)
from .queries import (
    ObtenerCampanaPorIdQuery, ListarCampanasQuery, ObtenerMetricasCampanaQuery,
    ObtenerEstadisticasGeneralesQuery
)

# Command Handlers

class CrearCampanaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, comando: CrearCampanaCommand) -> Campana:
        # Crear objetos valor
        tipo = TipoCampana(comando.tipo)
        moneda = Moneda(comando.presupuesto_moneda)
        presupuesto = Presupuesto(comando.presupuesto_monto, moneda)
        
        # Crear el agregado
        campana = Campana(
            nombre=comando.nombre,
            tipo=tipo,
            presupuesto=presupuesto,
            fecha_inicio=comando.fecha_inicio,
            fecha_fin=comando.fecha_fin,
            id_afiliado=comando.id_afiliado,
            descripcion=comando.descripcion,
            id_campana=comando.id_campana
        )
        
        # Persistir
        self.repositorio.agregar(campana)
        
        return campana

class ActualizarPresupuestoCampanaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, comando: ActualizarPresupuestoCampanaCommand) -> Campana:
        campana = self.repositorio.obtener_por_id(comando.id_campana)
        if not campana:
            raise ValueError(f"Campaña con ID {comando.id_campana} no encontrada")
        
        # Crear nuevo presupuesto
        moneda = Moneda(comando.nueva_moneda)
        nuevo_presupuesto = Presupuesto(comando.nuevo_presupuesto_monto, moneda)
        
        # Actualizar
        campana.actualizar_presupuesto(nuevo_presupuesto)
        self.repositorio.actualizar(campana)
        
        return campana

class ActivarCampanaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, comando: ActivarCampanaCommand) -> Campana:
        campana = self.repositorio.obtener_por_id(comando.id_campana)
        if not campana:
            raise ValueError(f"Campaña con ID {comando.id_campana} no encontrada")
        
        # Activar
        campana.activar()
        self.repositorio.actualizar(campana)
        
        return campana

class ActualizarInformacionCampanaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, comando: ActualizarInformacionCampanaCommand) -> Campana:
        campana = self.repositorio.obtener_por_id(comando.id_campana)
        if not campana:
            raise ValueError(f"Campaña con ID {comando.id_campana} no encontrada")
        
        # Actualizar información
        campana.actualizar_informacion(
            nombre=comando.nombre,
            descripcion=comando.descripcion,
            fecha_inicio=comando.fecha_inicio,
            fecha_fin=comando.fecha_fin
        )
        self.repositorio.actualizar(campana)
        
        return campana

class ActualizarMetricasCampanaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, comando: ActualizarMetricasCampanaCommand) -> Campana:
        campana = self.repositorio.obtener_por_id(comando.id_campana)
        if not campana:
            raise ValueError(f"Campaña con ID {comando.id_campana} no encontrada")
        
        # Actualizar métricas
        campana.actualizar_metricas(
            impresiones=comando.impresiones,
            clicks=comando.clicks,
            conversiones=comando.conversiones,
            gasto_actual=comando.gasto_actual
        )
        self.repositorio.actualizar(campana)
        
        return campana

class PausarCampanaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, comando: PausarCampanaCommand) -> Campana:
        campana = self.repositorio.obtener_por_id(comando.id_campana)
        if not campana:
            raise ValueError(f"Campaña con ID {comando.id_campana} no encontrada")
        
        campana.pausar()
        self.repositorio.actualizar(campana)
        
        return campana

class FinalizarCampanaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, comando: FinalizarCampanaCommand) -> Campana:
        campana = self.repositorio.obtener_por_id(comando.id_campana)
        if not campana:
            raise ValueError(f"Campaña con ID {comando.id_campana} no encontrada")
        
        campana.finalizar()
        self.repositorio.actualizar(campana)
        
        return campana

class CancelarCampanaHandler(ComandoHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, comando: CancelarCampanaCommand) -> Campana:
        campana = self.repositorio.obtener_por_id(comando.id_campana)
        if not campana:
            raise ValueError(f"Campaña con ID {comando.id_campana} no encontrada")
        
        campana.cancelar()
        self.repositorio.actualizar(campana)
        
        return campana

# Query Handlers

class ObtenerCampanaPorIdHandler(QueryHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, query: ObtenerCampanaPorIdQuery) -> QueryResultado:
        campana = self.repositorio.obtener_por_id(query.id_campana)
        
        if not campana:
            return QueryResultado(resultado=None)
        
        resultado = self._mapear_campana_a_dict(campana)
        return QueryResultado(resultado=resultado)
    
    def _mapear_campana_a_dict(self, campana: Campana) -> Dict[str, Any]:
        return {
            "id": str(campana.id),
            "nombre": campana.nombre,
            "tipo": campana.tipo.value,
            "descripcion": campana.descripcion,
            "estado": campana.estado.value,
            "presupuesto": {
                "monto": float(campana.presupuesto.monto),
                "moneda": campana.presupuesto.moneda.value
            },
            "fecha_inicio": campana.fecha_inicio.isoformat(),
            "fecha_fin": campana.fecha_fin.isoformat(),
            "fecha_creacion": campana.fecha_creacion.isoformat(),
            "fecha_actualizacion": campana.fecha_actualizacion.isoformat(),
            "id_afiliado": campana.id_afiliado,
            "metricas": {
                "impresiones": campana.metricas.impresiones,
                "clicks": campana.metricas.clicks,
                "conversiones": campana.metricas.conversiones,
                "gasto_actual": float(campana.metricas.gasto_actual),
                "ctr": campana.metricas.ctr,
                "tasa_conversion": campana.metricas.tasa_conversion
            }
        }

class ListarCampanasHandler(QueryHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, query: ListarCampanasQuery) -> QueryResultado:
        if query.id_afiliado:
            campanas = self.repositorio.obtener_por_afiliado(
                query.id_afiliado, query.limit, query.offset
            )
        else:
            campanas = self.repositorio.listar(query.limit, query.offset)
        
        resultado = {
            "campanas": [self._mapear_campana_a_dict(campana) for campana in campanas],
            "total": len(campanas),
            "limit": query.limit,
            "offset": query.offset
        }
        
        return QueryResultado(resultado=resultado)
    
    def _mapear_campana_a_dict(self, campana: Campana) -> Dict[str, Any]:
        return {
            "id": str(campana.id),
            "nombre": campana.nombre,
            "tipo": campana.tipo.value,
            "estado": campana.estado.value,
            "presupuesto": {
                "monto": float(campana.presupuesto.monto),
                "moneda": campana.presupuesto.moneda.value
            },
            "fecha_inicio": campana.fecha_inicio.isoformat(),
            "fecha_fin": campana.fecha_fin.isoformat(),
            "id_afiliado": campana.id_afiliado,
            "metricas": {
                "impresiones": campana.metricas.impresiones,
                "clicks": campana.metricas.clicks,
                "conversiones": campana.metricas.conversiones,
                "gasto_actual": float(campana.metricas.gasto_actual)
            }
        }

class ObtenerMetricasCampanaHandler(QueryHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
        self.servicio_metricas = ServicioMetricasImpl()
        self.servicio_optimizacion = ServicioOptimizacionImpl()
    
    def handle(self, query: ObtenerMetricasCampanaQuery) -> QueryResultado:
        campana = self.repositorio.obtener_por_id(query.id_campana)
        
        if not campana:
            return QueryResultado(resultado=None)
        
        resultado = {
            "id_campana": str(campana.id),
            "metricas_basicas": {
                "impresiones": campana.metricas.impresiones,
                "clicks": campana.metricas.clicks,
                "conversiones": campana.metricas.conversiones,
                "gasto_actual": float(campana.metricas.gasto_actual),
                "ctr": campana.metricas.ctr,
                "tasa_conversion": campana.metricas.tasa_conversion
            },
            "metricas_calculadas": {
                "roi": float(self.servicio_metricas.calcular_roi(campana)),
                "cpc": float(self.servicio_metricas.calcular_cpc(campana)),
                "cpa": float(self.servicio_metricas.calcular_cpa(campana))
            },
            "rendimiento": self.servicio_optimizacion.evaluar_rendimiento(campana),
            "optimizaciones": self.servicio_optimizacion.sugerir_optimizaciones(campana)
        }
        
        return QueryResultado(resultado=resultado)

class ObtenerEstadisticasGeneralesHandler(QueryHandler):
    def __init__(self, repositorio: RepositorioCampanas):
        self.repositorio = repositorio
    
    def handle(self, query: ObtenerEstadisticasGeneralesQuery) -> QueryResultado:
        if query.id_afiliado:
            campanas = self.repositorio.obtener_por_afiliado(query.id_afiliado, limit=1000, offset=0)
        else:
            campanas = self.repositorio.listar(limit=1000, offset=0)
        
        # Calcular estadísticas agregadas
        total_campanas = len(campanas)
        total_impresiones = sum(c.metricas.impresiones for c in campanas)
        total_clicks = sum(c.metricas.clicks for c in campanas)
        total_conversiones = sum(c.metricas.conversiones for c in campanas)
        total_gasto = sum(c.metricas.gasto_actual for c in campanas)
        
        # Estadísticas por estado
        estados = {}
        for campana in campanas:
            estado = campana.estado.value
            if estado not in estados:
                estados[estado] = 0
            estados[estado] += 1
        
        resultado = {
            "total_campanas": total_campanas,
            "metricas_agregadas": {
                "total_impresiones": total_impresiones,
                "total_clicks": total_clicks,
                "total_conversiones": total_conversiones,
                "total_gasto": float(total_gasto),
                "ctr_promedio": (total_clicks / total_impresiones * 100) if total_impresiones > 0 else 0,
                "tasa_conversion_promedio": (total_conversiones / total_clicks * 100) if total_clicks > 0 else 0
            },
            "distribucion_por_estado": estados,
            "id_afiliado": query.id_afiliado
        }
        
        return QueryResultado(resultado=resultado)
