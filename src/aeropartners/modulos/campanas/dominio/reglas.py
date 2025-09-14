from datetime import datetime
from decimal import Decimal
from ....seedwork.dominio.reglas import ReglaNegocio

class CampanaNoPuedeSerActivadaSinPresupuesto(ReglaNegocio):
    def __init__(self, campana):
        self.campana = campana
        super().__init__("La campaña no puede ser activada sin un presupuesto válido")
    
    def es_valido(self) -> bool:
        return self.campana.presupuesto.monto > 0

class CampanaNoPuedeSerActivadaSinFechas(ReglaNegocio):
    def __init__(self, campana):
        self.campana = campana
        super().__init__("La campaña no puede ser activada sin fechas de inicio y fin válidas")
    
    def es_valido(self) -> bool:
        ahora = datetime.now()
        return (self.campana.fecha_inicio is not None and 
                self.campana.fecha_fin is not None and
                self.campana.fecha_inicio <= self.campana.fecha_fin and
                self.campana.fecha_fin > ahora)

class CampanaNoSePuedeActivarSiYaEstaActiva(ReglaNegocio):
    def __init__(self, campana):
        self.campana = campana
        super().__init__("La campaña no puede ser activada porque ya está activa")
    
    def es_valido(self) -> bool:
        from .enums import EstadoCampana
        return self.campana.estado != EstadoCampana.ACTIVA

class PresupuestoNoPuedeExcederLimite(ReglaNegocio):
    def __init__(self, nuevo_presupuesto: Decimal, limite: Decimal = Decimal('1000000')):
        self.nuevo_presupuesto = nuevo_presupuesto
        self.limite = limite
        super().__init__(f"El presupuesto no puede exceder {limite}")
    
    def es_valido(self) -> bool:
        return self.nuevo_presupuesto <= self.limite

class CampanaNoSePuedeModificarSiEstaFinalizada(ReglaNegocio):
    def __init__(self, campana):
        self.campana = campana
        super().__init__("La campaña no puede ser modificada porque está finalizada")
    
    def es_valido(self) -> bool:
        from .enums import EstadoCampana
        return self.campana.estado not in [EstadoCampana.FINALIZADA, EstadoCampana.CANCELADA]

class GastoNoPuedeExcederPresupuesto(ReglaNegocio):
    def __init__(self, gasto_actual: Decimal, presupuesto: Decimal):
        self.gasto_actual = gasto_actual
        self.presupuesto = presupuesto
        super().__init__("El gasto actual no puede exceder el presupuesto de la campaña")
    
    def es_valido(self) -> bool:
        return self.gasto_actual <= self.presupuesto
