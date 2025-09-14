from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any
from .entidades import Campana

class ServicioMetricas(ABC):
    """Servicio de dominio para el cálculo de métricas de campaña"""
    
    @abstractmethod
    def calcular_roi(self, campana: Campana) -> Decimal:
        """Calcular el ROI (Return on Investment) de una campaña"""
        pass
    
    @abstractmethod
    def calcular_cpc(self, campana: Campana) -> Decimal:
        """Calcular el CPC (Cost per Click) de una campaña"""
        pass
    
    @abstractmethod
    def calcular_cpa(self, campana: Campana) -> Decimal:
        """Calcular el CPA (Cost per Acquisition) de una campaña"""
        pass

class ServicioOptimizacion(ABC):
    """Servicio de dominio para optimización de campañas"""
    
    @abstractmethod
    def sugerir_optimizaciones(self, campana: Campana) -> Dict[str, Any]:
        """Sugerir optimizaciones para una campaña"""
        pass
    
    @abstractmethod
    def evaluar_rendimiento(self, campana: Campana) -> str:
        """Evaluar el rendimiento de una campaña"""
        pass

class ServicioMetricasImpl(ServicioMetricas):
    """Implementación del servicio de métricas"""
    
    def calcular_roi(self, campana: Campana) -> Decimal:
        """Calcular ROI: (Ingresos - Inversión) / Inversión * 100"""
        if campana.metricas.gasto_actual == 0:
            return Decimal('0')
        
        # Asumimos un valor promedio por conversión para el cálculo
        valor_por_conversion = Decimal('50')  # Este valor debería venir de configuración
        ingresos = campana.metricas.conversiones * valor_por_conversion
        
        roi = ((ingresos - campana.metricas.gasto_actual) / campana.metricas.gasto_actual) * 100
        return roi.quantize(Decimal('0.01'))
    
    def calcular_cpc(self, campana: Campana) -> Decimal:
        """Calcular CPC: Gasto Total / Total de Clicks"""
        if campana.metricas.clicks == 0:
            return Decimal('0')
        
        cpc = campana.metricas.gasto_actual / campana.metricas.clicks
        return cpc.quantize(Decimal('0.01'))
    
    def calcular_cpa(self, campana: Campana) -> Decimal:
        """Calcular CPA: Gasto Total / Total de Conversiones"""
        if campana.metricas.conversiones == 0:
            return Decimal('0')
        
        cpa = campana.metricas.gasto_actual / campana.metricas.conversiones
        return cpa.quantize(Decimal('0.01'))

class ServicioOptimizacionImpl(ServicioOptimizacion):
    """Implementación del servicio de optimización"""
    
    def sugerir_optimizaciones(self, campana: Campana) -> Dict[str, Any]:
        """Sugerir optimizaciones basadas en las métricas actuales"""
        sugerencias = []
        
        # Evaluar CTR
        if campana.metricas.ctr < 1.0:
            sugerencias.append({
                "tipo": "CTR_BAJO",
                "mensaje": "El CTR está por debajo del 1%. Considera mejorar el copy o las imágenes.",
                "prioridad": "ALTA"
            })
        
        # Evaluar tasa de conversión
        if campana.metricas.tasa_conversion < 2.0:
            sugerencias.append({
                "tipo": "CONVERSION_BAJA",
                "mensaje": "La tasa de conversión está por debajo del 2%. Revisa la página de destino.",
                "prioridad": "MEDIA"
            })
        
        # Evaluar gasto vs presupuesto
        porcentaje_gasto = (campana.metricas.gasto_actual / campana.presupuesto.monto) * 100
        if porcentaje_gasto > 80:
            sugerencias.append({
                "tipo": "PRESUPUESTO_ALTO",
                "mensaje": f"Has gastado el {porcentaje_gasto:.1f}% del presupuesto. Considera aumentarlo si la campaña está funcionando bien.",
                "prioridad": "MEDIA"
            })
        
        return {
            "sugerencias": sugerencias,
            "total_sugerencias": len(sugerencias)
        }
    
    def evaluar_rendimiento(self, campana: Campana) -> str:
        """Evaluar el rendimiento general de la campaña"""
        servicio_metricas = ServicioMetricasImpl()
        roi = servicio_metricas.calcular_roi(campana)
        ctr = campana.metricas.ctr
        tasa_conversion = campana.metricas.tasa_conversion
        
        # Lógica simple de evaluación
        if roi > 100 and ctr > 2.0 and tasa_conversion > 3.0:
            return "EXCELENTE"
        elif roi > 50 and ctr > 1.5 and tasa_conversion > 2.0:
            return "BUENO"
        elif roi > 0 and ctr > 1.0 and tasa_conversion > 1.0:
            return "REGULAR"
        else:
            return "DEFICIENTE"
