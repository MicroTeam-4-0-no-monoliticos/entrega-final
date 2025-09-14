from decimal import Decimal
from ..dominio.entidades import Campana
from ..dominio.enums import EstadoCampana, TipoCampana
from ..dominio.objetos_valor import Presupuesto, MetricasCampana
from ....seedwork.dominio.objetos_valor import Moneda
from .modelos import CampanaModel

class MapeadorCampana:
    """Mapeador entre entidad de dominio y modelo de base de datos"""
    
    @staticmethod
    def entidad_a_modelo(campana: Campana) -> CampanaModel:
        """Convierte una entidad de dominio a un modelo de base de datos"""
        return CampanaModel(
            id=campana.id,
            nombre=campana.nombre,
            tipo=campana.tipo.value,
            descripcion=campana.descripcion,
            estado=campana.estado.value,
            presupuesto_monto=float(campana.presupuesto.monto),
            presupuesto_moneda=campana.presupuesto.moneda.value,
            fecha_inicio=campana.fecha_inicio,
            fecha_fin=campana.fecha_fin,
            fecha_creacion=campana.fecha_creacion,
            fecha_actualizacion=campana.fecha_actualizacion,
            impresiones=campana.metricas.impresiones,
            clicks=campana.metricas.clicks,
            conversiones=campana.metricas.conversiones,
            gasto_actual=float(campana.metricas.gasto_actual),
            id_afiliado=campana.id_afiliado
        )
    
    @staticmethod
    def modelo_a_entidad(modelo: CampanaModel) -> Campana:
        """Convierte un modelo de base de datos a una entidad de dominio"""
        # Crear objetos valor
        moneda = Moneda(modelo.presupuesto_moneda)
        presupuesto = Presupuesto(Decimal(str(modelo.presupuesto_monto)), moneda)
        metricas = MetricasCampana(
            impresiones=modelo.impresiones,
            clicks=modelo.clicks,
            conversiones=modelo.conversiones,
            gasto_actual=Decimal(str(modelo.gasto_actual))
        )
        
        # Crear la entidad
        campana = Campana(
            nombre=modelo.nombre,
            tipo=TipoCampana(modelo.tipo),
            presupuesto=presupuesto,
            fecha_inicio=modelo.fecha_inicio,
            fecha_fin=modelo.fecha_fin,
            id_afiliado=modelo.id_afiliado,
            descripcion=modelo.descripcion,
            id_campana=modelo.id
        )
        
        # Establecer propiedades que no se pasan en el constructor
        campana.estado = EstadoCampana(modelo.estado)
        campana.metricas = metricas
        campana.fecha_creacion = modelo.fecha_creacion
        campana.fecha_actualizacion = modelo.fecha_actualizacion
        
        # Limpiar eventos (no queremos replicar eventos al cargar desde BD)
        campana.limpiar_eventos()
        
        return campana
    
    @staticmethod
    def actualizar_modelo_desde_entidad(modelo: CampanaModel, campana: Campana) -> CampanaModel:
        """Actualiza un modelo existente con los datos de una entidad"""
        modelo.nombre = campana.nombre
        modelo.tipo = campana.tipo.value
        modelo.descripcion = campana.descripcion
        modelo.estado = campana.estado.value
        modelo.presupuesto_monto = float(campana.presupuesto.monto)
        modelo.presupuesto_moneda = campana.presupuesto.moneda.value
        modelo.fecha_inicio = campana.fecha_inicio
        modelo.fecha_fin = campana.fecha_fin
        modelo.fecha_actualizacion = campana.fecha_actualizacion
        modelo.impresiones = campana.metricas.impresiones
        modelo.clicks = campana.metricas.clicks
        modelo.conversiones = campana.metricas.conversiones
        modelo.gasto_actual = float(campana.metricas.gasto_actual)
        modelo.id_afiliado = campana.id_afiliado
        
        return modelo
