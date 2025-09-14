import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from .enums import EstadoCampana, TipoCampana
from .objetos_valor import Presupuesto, MetricasCampana
from .eventos import CampanaCreada, CampanaActualizada, CampanaActivada, PresupuestoCampanaActualizado, MetricasCampanaActualizadas
from .reglas import (
    CampanaNoPuedeSerActivadaSinPresupuesto,
    CampanaNoPuedeSerActivadaSinFechas,
    CampanaNoSePuedeActivarSiYaEstaActiva,
    CampanaNoSePuedeModificarSiEstaFinalizada,
    PresupuestoNoPuedeExcederLimite,
    GastoNoPuedeExcederPresupuesto
)
from ....seedwork.dominio.objetos_valor import Moneda

class Campana:
    """Agregado raíz para el dominio de campañas"""
    
    def __init__(
        self, 
        nombre: str, 
        tipo: TipoCampana,
        presupuesto: Presupuesto,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        id_afiliado: str,
        descripcion: Optional[str] = None,
        id_campana: Optional[uuid.UUID] = None
    ):
        self.id = id_campana or uuid.uuid4()
        self.nombre = nombre
        self.tipo = tipo
        self.presupuesto = presupuesto
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.id_afiliado = id_afiliado
        self.descripcion = descripcion
        self.estado = EstadoCampana.BORRADOR
        self.metricas = MetricasCampana()
        self.fecha_creacion = datetime.now()
        self.fecha_actualizacion = datetime.now()
        self.eventos: List = []
        
        # Generar evento de creación
        self.agregar_evento(CampanaCreada(
            id_campana=str(self.id),
            nombre=self.nombre,
            tipo=self.tipo.value,
            presupuesto_monto=self.presupuesto.monto,
            presupuesto_moneda=self.presupuesto.moneda.value,
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin,
            estado=self.estado.value,
            id_afiliado=self.id_afiliado
        ))
    
    def agregar_evento(self, evento):
        """Agregar evento de dominio"""
        self.eventos.append(evento)
    
    def limpiar_eventos(self):
        """Limpiar eventos de dominio"""
        self.eventos = []
    
    def validar_regla(self, regla):
        """Validar una regla de negocio"""
        if not regla.es_valido():
            raise Exception(regla.mensaje)
    
    def activar(self):
        """Activar la campaña siguiendo las reglas de negocio"""
        # Validar reglas de negocio
        self.validar_regla(CampanaNoPuedeSerActivadaSinPresupuesto(self))
        self.validar_regla(CampanaNoPuedeSerActivadaSinFechas(self))
        self.validar_regla(CampanaNoSePuedeActivarSiYaEstaActiva(self))
        
        # Cambiar estado
        self.estado = EstadoCampana.ACTIVA
        self.fecha_actualizacion = datetime.now()
        
        # Generar evento
        self.agregar_evento(CampanaActivada(
            id_campana=str(self.id),
            nombre=self.nombre,
            fecha_activacion=datetime.now()
        ))
    
    def actualizar_presupuesto(self, nuevo_presupuesto: Presupuesto):
        """Actualizar el presupuesto de la campaña"""
        # Validar reglas de negocio
        self.validar_regla(CampanaNoSePuedeModificarSiEstaFinalizada(self))
        self.validar_regla(PresupuestoNoPuedeExcederLimite(nuevo_presupuesto.monto))
        self.validar_regla(GastoNoPuedeExcederPresupuesto(self.metricas.gasto_actual, nuevo_presupuesto.monto))
        
        presupuesto_anterior = self.presupuesto.monto
        self.presupuesto = nuevo_presupuesto
        self.fecha_actualizacion = datetime.now()
        
        # Generar evento
        self.agregar_evento(PresupuestoCampanaActualizado(
            id_campana=str(self.id),
            presupuesto_anterior=presupuesto_anterior,
            presupuesto_nuevo=nuevo_presupuesto.monto,
            moneda=nuevo_presupuesto.moneda.value
        ))
    
    def actualizar_informacion(self, nombre: Optional[str] = None, descripcion: Optional[str] = None, 
                             fecha_inicio: Optional[datetime] = None, fecha_fin: Optional[datetime] = None):
        """Actualizar información básica de la campaña"""
        # Validar reglas de negocio
        self.validar_regla(CampanaNoSePuedeModificarSiEstaFinalizada(self))
        
        if nombre:
            self.nombre = nombre
        if descripcion is not None:
            self.descripcion = descripcion
        if fecha_inicio:
            self.fecha_inicio = fecha_inicio
        if fecha_fin:
            self.fecha_fin = fecha_fin
            
        self.fecha_actualizacion = datetime.now()
        
        # Generar evento
        self.agregar_evento(CampanaActualizada(
            id_campana=str(self.id),
            nombre=self.nombre,
            presupuesto_monto=self.presupuesto.monto,
            presupuesto_moneda=self.presupuesto.moneda.value,
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin,
            estado=self.estado.value
        ))
    
    def actualizar_metricas(self, impresiones: int = None, clicks: int = None, 
                           conversiones: int = None, gasto_actual: Decimal = None):
        """Actualizar las métricas de la campaña"""
        # Crear nuevas métricas con los valores actualizados
        nuevas_metricas = MetricasCampana(
            impresiones=impresiones if impresiones is not None else self.metricas.impresiones,
            clicks=clicks if clicks is not None else self.metricas.clicks,
            conversiones=conversiones if conversiones is not None else self.metricas.conversiones,
            gasto_actual=gasto_actual if gasto_actual is not None else self.metricas.gasto_actual
        )
        
        # Validar que el gasto no exceda el presupuesto
        self.validar_regla(GastoNoPuedeExcederPresupuesto(nuevas_metricas.gasto_actual, self.presupuesto.monto))
        
        self.metricas = nuevas_metricas
        self.fecha_actualizacion = datetime.now()
        
        # Generar evento
        self.agregar_evento(MetricasCampanaActualizadas(
            id_campana=str(self.id),
            impresiones=self.metricas.impresiones,
            clicks=self.metricas.clicks,
            conversiones=self.metricas.conversiones,
            gasto_actual=self.metricas.gasto_actual
        ))
    
    def pausar(self):
        """Pausar la campaña"""
        self.validar_regla(CampanaNoSePuedeModificarSiEstaFinalizada(self))
        self.estado = EstadoCampana.PAUSADA
        self.fecha_actualizacion = datetime.now()
    
    def finalizar(self):
        """Finalizar la campaña"""
        self.estado = EstadoCampana.FINALIZADA
        self.fecha_actualizacion = datetime.now()
    
    def cancelar(self):
        """Cancelar la campaña"""
        self.estado = EstadoCampana.CANCELADA
        self.fecha_actualizacion = datetime.now()
