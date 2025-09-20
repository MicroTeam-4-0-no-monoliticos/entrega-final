import random
import time
from typing import Optional
import uuid
from ..dominio.servicios import PasarelaDePagos, ResultadoPago
from ..dominio.repositorios import RepositorioPagos
from ..dominio.entidades import Pago
from ....seedwork.infraestructura.db import SessionLocal
from .mapeadores import MapeadorPago
from .modelos import PagoModel, OutboxModel

class StripeAdapter(PasarelaDePagos):
    """Adaptador mock para Stripe que simula llamadas a la API externa"""
    
    def __init__(self, base_url: str = "https://api.stripe.com/v1"):
        self.base_url = base_url
        self.api_key = "sk_test_mock_key"
    
    def procesar_pago(self, referencia: str, monto: float, moneda: str, id_afiliado: str) -> ResultadoPago:
        """
        Simula el procesamiento de un pago a través de Stripe
        En un escenario real, aquí se haría la llamada HTTP a la API de Stripe
        """
        time.sleep(random.uniform(2.0, 8.0))
        
        # Simular éxito/fallo aleatorio (90% éxito, 10% fallo)
        if random.random() < 0.9:
            return ResultadoPago(
                exitoso=True,
                referencia_transaccion=f"txn_{random.randint(100000, 999999)}"
            )
        else:
            errores_posibles = [
                "Fondos insuficientes",
                "Tarjeta expirada",
                "Tarjeta rechazada",
                "Error de conexión con el banco"
            ]
            return ResultadoPago(
                exitoso=False,
                mensaje_error=random.choice(errores_posibles)
            )

class RepositorioPagosSQLAlchemy(RepositorioPagos):
    """Implementación del repositorio de pagos usando SQLAlchemy"""
    
    def __init__(self):
        self.mapeador = MapeadorPago()
    
    def obtener_por_id(self, id: uuid.UUID) -> Optional[Pago]:
        db = SessionLocal()
        try:
            modelo = db.query(PagoModel).filter(PagoModel.id == str(id)).first()
            return self.mapeador.entidad_a_dto(modelo) if modelo else None
        finally:
            db.close()
    
    def obtener_por_referencia(self, referencia: str) -> Optional[Pago]:
        db = SessionLocal()
        try:
            modelo = db.query(PagoModel).filter(PagoModel.referencia_pago == referencia).first()
            return self.mapeador.entidad_a_dto(modelo) if modelo else None
        finally:
            db.close()
    
    def agregar(self, pago: Pago):
        db = SessionLocal()
        try:
            modelo = self.mapeador.dto_a_entidad(pago)
            db.add(modelo)
            
            # Agregar eventos al outbox
            for evento in pago.eventos:
                outbox_evento = OutboxModel(
                    id=uuid.uuid4(),
                    tipo_evento=type(evento).__name__,
                    datos_evento=self._serializar_evento(evento),
                    procesado=False
                )
                db.add(outbox_evento)
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def actualizar(self, pago: Pago):
        db = SessionLocal()
        try:
            modelo = db.query(PagoModel).filter(PagoModel.id == str(pago.id)).first()
            if modelo:
                modelo.estado = pago.estado.value
                modelo.fecha_procesamiento = pago.fecha_procesamiento
                modelo.mensaje_error = pago.mensaje_error
                modelo.fecha_actualizacion = pago.fecha_actualizacion
                
                # Agregar nuevos eventos al outbox
                for evento in pago.eventos:
                    outbox_evento = OutboxModel(
                        id=uuid.uuid4(),
                        tipo_evento=type(evento).__name__,
                        datos_evento=self._serializar_evento(evento),
                        procesado=False
                    )
                    db.add(outbox_evento)
                
                db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def eliminar(self, pago: Pago):
        db = SessionLocal()
        try:
            modelo = db.query(PagoModel).filter(PagoModel.id == str(pago.id)).first()
            if modelo:
                db.delete(modelo)
                db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def obtener_todos(self):
        """Obtener todos los pagos"""
        db = SessionLocal()
        try:
            modelos = db.query(PagoModel).all()
            pagos = []
            for modelo in modelos:
                pago = self._reconstruir_pago(modelo)
                pagos.append(pago)
            return pagos
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def _reconstruir_pago(self, modelo: PagoModel) -> Pago:
        """Reconstruir entidad Pago desde el modelo de base de datos"""
        from ..dominio.objetos_valor import Dinero, Moneda
        from ..dominio.enums import EstadoPago
        
        pago = Pago(
            id_afiliado=modelo.id_afiliado,
            monto=Dinero(modelo.monto, Moneda(modelo.moneda)),
            referencia_pago=modelo.referencia_pago
        )
        pago.id = modelo.id
        pago.estado = EstadoPago(modelo.estado)
        pago.fecha_creacion = modelo.fecha_creacion
        pago.fecha_actualizacion = modelo.fecha_actualizacion
        pago.fecha_procesamiento = modelo.fecha_procesamiento
        pago.mensaje_error = modelo.mensaje_error
        
        return pago
    
    def _serializar_evento(self, evento) -> str:
        """Serializa un evento de dominio a JSON"""
        import json
        return json.dumps({
            "id": str(evento.id),
            "fecha_evento": evento.fecha_evento.isoformat(),
            **{k: v for k, v in evento.__dict__.items() if k not in ['id', 'fecha_evento']}
        }, default=str)
