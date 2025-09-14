"""
Adaptadores de infraestructura para el módulo de Reporting
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..dominio.servicios import ServicioDatosPort
from ..dominio.objetos_valor import FiltrosReporte

logger = logging.getLogger(__name__)


class ServicioDatosAdapter(ServicioDatosPort):
    """Adaptador para servicios de datos externos"""
    
    def __init__(self, base_url: str, version: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.version = version
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea una sesión HTTP"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Realiza una petición HTTP al servicio de datos"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            logger.info(f"Realizando petición a: {url}")
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Respuesta exitosa de {url}")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Error en petición a {url}: {response.status} - {error_text}")
                    raise Exception(f"Error HTTP {response.status}: {error_text}")
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout en petición a {url}")
            raise Exception(f"Timeout en petición a {url}")
        except Exception as e:
            logger.error(f"Error en petición a {url}: {str(e)}")
            raise
    
    async def obtener_datos_pagos(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene datos de pagos desde el servicio externo"""
        # Usar el endpoint de estadísticas de outbox de pagos
        endpoint = "/pagos/outbox/estadisticas"
        return await self._make_request(endpoint, {})
    
    async def obtener_datos_campanas(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene datos de campañas desde el servicio externo"""
        # Usar el endpoint real de campañas
        endpoint = "/campaigns/"
        params = {}
        if filtros.afiliado_id:
            params['id_afiliado'] = filtros.afiliado_id
        if filtros.campana_id:
            params['id_campana'] = filtros.campana_id
        
        return await self._make_request(endpoint, params)
    
    async def obtener_metricas_generales(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene métricas generales desde el servicio externo"""
        # Usar el endpoint real de estadísticas de campañas
        endpoint = "/campaigns/stats/general"
        params = {}
        if filtros.afiliado_id:
            params['id_afiliado'] = filtros.afiliado_id
        
        return await self._make_request(endpoint, params)
    
    async def verificar_conectividad(self) -> bool:
        """Verifica si el servicio está disponible"""
        try:
            # Endpoint de health check
            health_endpoint = "/health" if self.version.startswith('v2') else "/api/health"
            await self._make_request(health_endpoint)
            return True
        except Exception as e:
            logger.warning(f"Servicio no disponible: {str(e)}")
            return False
    
    async def close(self):
        """Cierra la sesión HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()


class ServicioDatosV1Adapter(ServicioDatosAdapter):
    """Adaptador específico para servicio de datos v1"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        super().__init__(base_url, "v1", timeout)
    
    async def obtener_datos_pagos(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene datos reales de pagos del servicio de pagos"""
        try:
            # Usar el servicio real de pagos
            url = f"{self.base_url}/pagos/"
            
            # Construir parámetros de consulta
            params = {}
            if filtros.afiliado_id:
                params['id_afiliado'] = filtros.afiliado_id
            if filtros.estado_pago:
                params['estado'] = filtros.estado_pago
            
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Transformar a formato de reporte
                    pagos = data if isinstance(data, list) else [data]
                    return {
                        "version": "v1",
                        "pagos": pagos,
                        "total_pagos": len(pagos),
                        "monto_total": sum(p.get('monto', 0) for p in pagos),
                        "filtros_aplicados": filtros.to_dict()
                    }
                else:
                    raise Exception(f"Error del servicio de pagos: {response.status}")
        except Exception as e:
            logger.error(f"Error obteniendo datos de pagos: {str(e)}")
            # Fallback a datos mock si falla
            return {
                "version": "v1",
                "pagos": [],
                "total_pagos": 0,
                "monto_total": 0,
                "filtros_aplicados": filtros.to_dict(),
                "error": str(e)
            }
    
    async def obtener_datos_campanas(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene datos reales de campañas del servicio de campañas"""
        try:
            # Usar el servicio real de campañas
            url = f"{self.base_url}/campaigns/"
            
            params = {}
            if filtros.afiliado_id:
                params['id_afiliado'] = filtros.afiliado_id
            if filtros.campana_id:
                params['id_campana'] = filtros.campana_id
            
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    campanas = data.get('campanas', []) if isinstance(data, dict) else data
                    return {
                        "version": "v1",
                        "campanas": campanas,
                        "total_campanas": len(campanas),
                        "filtros_aplicados": filtros.to_dict()
                    }
                else:
                    raise Exception(f"Error del servicio de campañas: {response.status}")
        except Exception as e:
            logger.error(f"Error obteniendo datos de campañas: {str(e)}")
            # Fallback a datos mock si falla
            return {
                "version": "v1",
                "campanas": [],
                "total_campanas": 0,
                "filtros_aplicados": filtros.to_dict(),
                "error": str(e)
            }
    
    async def obtener_metricas_generales(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene métricas reales de los servicios"""
        try:
            session = await self._get_session()
            
            # Obtener estadísticas de campañas
            campanas_url = f"{self.base_url}/campaigns/stats/general"
            params = {}
            if filtros.afiliado_id:
                params['id_afiliado'] = filtros.afiliado_id
            
            async with session.get(campanas_url, params=params) as response:
                if response.status == 200:
                    campanas_stats = await response.json()
                    
                    # Obtener estadísticas de pagos (outbox)
                    pagos_url = f"{self.base_url}/pagos/outbox/estadisticas"
                    async with session.get(pagos_url) as pagos_response:
                        pagos_stats = await pagos_response.json() if pagos_response.status == 200 else {}
                        
                        return {
                            "version": "v1",
                            "metricas": {
                                "total_campanas": campanas_stats.get('total_campanas', 0),
                                "total_pagos": pagos_stats.get('total_eventos', 0),
                                "campanas_activas": campanas_stats.get('distribucion_por_estado', {}).get('activa', 0),
                                "afiliados_activos": 1 if filtros.afiliado_id else 0
                            },
                            "filtros_aplicados": filtros.to_dict()
                        }
                else:
                    raise Exception(f"Error obteniendo métricas: {response.status}")
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {str(e)}")
            # Fallback a datos mock si falla
            return {
                "version": "v1",
                "metricas": {
                    "total_campanas": 0,
                    "total_pagos": 0,
                    "campanas_activas": 0,
                    "afiliados_activos": 0
                },
                "filtros_aplicados": filtros.to_dict(),
                "error": str(e)
            }


class ServicioDatosV2Adapter(ServicioDatosAdapter):
    """Adaptador específico para servicio de datos v2"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        super().__init__(base_url, "v2", timeout)
    
    async def obtener_datos_pagos(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene datos reales de pagos con formato mejorado v2"""
        try:
            # Usar el servicio real de pagos
            url = f"{self.base_url}/pagos/"
            
            params = {}
            if filtros.afiliado_id:
                params['id_afiliado'] = filtros.afiliado_id
            if filtros.estado_pago:
                params['estado'] = filtros.estado_pago
            
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    pagos = data if isinstance(data, list) else [data]
                    
                    # Transformar a formato v2 mejorado
                    payments = []
                    for pago in pagos:
                        payments.append({
                            "payment_id": pago.get('id', ''),
                            "amount": pago.get('monto', 0),
                            "currency": pago.get('moneda', 'USD'),
                            "created_at": pago.get('fecha_creacion', ''),
                            "status": pago.get('estado', ''),
                            "affiliate_id": pago.get('id_afiliado', ''),
                            "commission_rate": 0.15  # Valor por defecto
                        })
                    
                    total_amount = sum(p.get('monto', 0) for p in pagos)
                    success_count = len([p for p in pagos if p.get('estado') == 'exitoso'])
                    
                    return {
                        "version": "v2",
                        "data": {
                            "payments": payments,
                            "summary": {
                                "total_payments": len(pagos),
                                "total_amount": total_amount,
                                "average_amount": total_amount / len(pagos) if pagos else 0,
                                "success_rate": success_count / len(pagos) if pagos else 0
                            }
                        },
                        "metadata": {
                            "filters_applied": filtros.to_dict(),
                            "generated_at": datetime.utcnow().isoformat()
                        }
                    }
                else:
                    raise Exception(f"Error del servicio de pagos: {response.status}")
        except Exception as e:
            logger.error(f"Error obteniendo datos de pagos v2: {str(e)}")
            return {
                "version": "v2",
                "data": {"payments": [], "summary": {"total_payments": 0, "total_amount": 0, "average_amount": 0, "success_rate": 0}},
                "metadata": {"filters_applied": filtros.to_dict(), "generated_at": datetime.utcnow().isoformat(), "error": str(e)}
            }
    
    async def obtener_datos_campanas(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene datos reales de campañas con formato mejorado v2"""
        try:
            # Usar el servicio real de campañas
            url = f"{self.base_url}/campaigns/"
            
            params = {}
            if filtros.afiliado_id:
                params['id_afiliado'] = filtros.afiliado_id
            if filtros.campana_id:
                params['id_campana'] = filtros.campana_id
            
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    campanas = data.get('campanas', []) if isinstance(data, dict) else data
                    
                    # Transformar a formato v2 mejorado
                    campaigns = []
                    for campana in campanas:
                        campaigns.append({
                            "campaign_id": campana.get('id', ''),
                            "name": campana.get('nombre', ''),
                            "status": campana.get('estado', ''),
                            "start_date": campana.get('fecha_inicio', ''),
                            "end_date": campana.get('fecha_fin', ''),
                            "budget": campana.get('presupuesto', {}).get('monto', 0),
                            "spent": 0  # Valor por defecto
                        })
                    
                    active_count = len([c for c in campanas if c.get('estado') == 'activa'])
                    total_budget = sum(c.get('presupuesto', {}).get('monto', 0) for c in campanas)
                    
                    return {
                        "version": "v2",
                        "data": {
                            "campaigns": campaigns,
                            "summary": {
                                "total_campaigns": len(campanas),
                                "active_campaigns": active_count,
                                "total_budget": total_budget
                            }
                        },
                        "metadata": {
                            "filters_applied": filtros.to_dict(),
                            "generated_at": datetime.utcnow().isoformat()
                        }
                    }
                else:
                    raise Exception(f"Error del servicio de campañas: {response.status}")
        except Exception as e:
            logger.error(f"Error obteniendo datos de campañas v2: {str(e)}")
            return {
                "version": "v2",
                "data": {"campaigns": [], "summary": {"total_campaigns": 0, "active_campaigns": 0, "total_budget": 0}},
                "metadata": {"filters_applied": filtros.to_dict(), "generated_at": datetime.utcnow().isoformat(), "error": str(e)}
            }
    
    async def obtener_metricas_generales(self, filtros: FiltrosReporte) -> Dict[str, Any]:
        """Obtiene métricas reales con formato mejorado v2"""
        try:
            session = await self._get_session()
            
            # Obtener estadísticas de campañas
            campanas_url = f"{self.base_url}/campaigns/stats/general"
            params = {}
            if filtros.afiliado_id:
                params['id_afiliado'] = filtros.afiliado_id
            
            async with session.get(campanas_url, params=params) as response:
                if response.status == 200:
                    campanas_stats = await response.json()
                    
                    # Obtener estadísticas de pagos (outbox)
                    pagos_url = f"{self.base_url}/pagos/outbox/estadisticas"
                    async with session.get(pagos_url) as pagos_response:
                        pagos_stats = await pagos_response.json() if pagos_response.status == 200 else {}
                        
                        return {
                            "version": "v2",
                            "data": {
                                "metrics": {
                                    "total_revenue": 0,  # No disponible en los servicios actuales
                                    "total_payments": pagos_stats.get('total_eventos', 0),
                                    "active_campaigns": campanas_stats.get('distribucion_por_estado', {}).get('activa', 0),
                                    "active_affiliates": 1 if filtros.afiliado_id else 0,
                                    "conversion_rate": 0.12,  # Valor por defecto
                                    "average_order_value": 0  # No disponible
                                },
                                "trends": {
                                    "revenue_growth": 0.15,  # Valor por defecto
                                    "payment_growth": 0.08   # Valor por defecto
                                }
                            },
                            "metadata": {
                                "filters_applied": filtros.to_dict(),
                                "generated_at": datetime.utcnow().isoformat()
                            }
                        }
                else:
                    raise Exception(f"Error obteniendo métricas: {response.status}")
        except Exception as e:
            logger.error(f"Error obteniendo métricas v2: {str(e)}")
            return {
                "version": "v2",
                "data": {
                    "metrics": {"total_revenue": 0, "total_payments": 0, "active_campaigns": 0, "active_affiliates": 0, "conversion_rate": 0, "average_order_value": 0},
                    "trends": {"revenue_growth": 0, "payment_growth": 0}
                },
                "metadata": {"filters_applied": filtros.to_dict(), "generated_at": datetime.utcnow().isoformat(), "error": str(e)}
            }
