import os
import asyncio
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import httpx
import uvicorn

PRIMARY = os.getenv("PRIMARY_SERVICE_URL", "http://campaigns-svc:8000").rstrip("/")
REPLICA = os.getenv("REPLICA_SERVICE_URL", "http://campaigns-svc-replica:8000").rstrip("/")
HEALTH_PATH = os.getenv("HEALTH_PATH", "/campaigns/healthz")
TIMEOUT = float(os.getenv("HEALTH_CHECK_TIMEOUT", "5"))
INTERVAL = float(os.getenv("HEALTH_CHECK_INTERVAL", "2"))
MAX_FAILS = int(os.getenv("MAX_CONSECUTIVE_FAILURES", "3"))

app = FastAPI(title="Campaigns Proxy", version="1.0.0")

@app.get("/")
async def root():
    """Información general del proxy de campañas"""
    return {
        "service": "campaigns-proxy",
        "version": "1.0.0",
        "description": "Proxy con failover automático para servicios de campañas",
        "endpoints": {
            "health": "/health",
            "status": "/status", 
            "campaigns_health": "/api/campaigns/health",
            "campaigns_api": "/api/campaigns/*"
        },
        "configuration": {
            "primary_service": PRIMARY,
            "replica_service": REPLICA,
            "health_check_interval": f"{INTERVAL}s",
            "max_consecutive_failures": MAX_FAILS,
            "health_check_timeout": f"{TIMEOUT}s"
        }
    }

_active: str = PRIMARY
_fail_counts = {PRIMARY: 0, REPLICA: 0}
_client = httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT))

async def check_health(url: str) -> bool:
    try:
        r = await _client.get(f"{url}{HEALTH_PATH}")
        return r.status_code == 200
    except Exception:
        return False

async def health_monitor():
    global _active
    while True:
        primary_ok, replica_ok = await asyncio.gather(check_health(PRIMARY), check_health(REPLICA))

        # actualizar contadores
        _fail_counts[PRIMARY] = 0 if primary_ok else _fail_counts[PRIMARY] + 1
        _fail_counts[REPLICA] = 0 if replica_ok else _fail_counts[REPLICA] + 1

        # lógica de failover / fallback
        if _active == PRIMARY and _fail_counts[PRIMARY] >= MAX_FAILS and replica_ok:
            _active = REPLICA
        elif _active == REPLICA and _fail_counts[REPLICA] >= MAX_FAILS and primary_ok:
            _active = PRIMARY

        await asyncio.sleep(INTERVAL)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(health_monitor())

@app.on_event("shutdown")
async def on_shutdown():
    await _client.aclose()

@app.get("/api/campaigns/health")
async def proxy_health():
    primary_ok, replica_ok = await asyncio.gather(check_health(PRIMARY), check_health(REPLICA))
    return {
        "primary": {"url": PRIMARY, "ok": primary_ok, "fail_count": _fail_counts[PRIMARY]},
        "replica": {"url": REPLICA, "ok": replica_ok, "fail_count": _fail_counts[REPLICA]},
        "active_target": _active,
    }

# Endpoint de health check general del proxy
@app.get("/health")
async def health_check():
    """Health check general del proxy"""
    primary_ok, replica_ok = await asyncio.gather(check_health(PRIMARY), check_health(REPLICA))
    
    # El proxy está sano si al menos uno de los servicios está funcionando
    proxy_healthy = primary_ok or replica_ok
    
    return {
        "status": "healthy" if proxy_healthy else "unhealthy",
        "service": "campaigns-proxy",
        "timestamp": datetime.now().isoformat(),
        "backends": {
            "primary": {"url": PRIMARY, "ok": primary_ok, "fail_count": _fail_counts[PRIMARY]},
            "replica": {"url": REPLICA, "ok": replica_ok, "fail_count": _fail_counts[REPLICA]},
            "active": _active
        }
    }

# Endpoint de status general del proxy
@app.get("/status")
async def status_check():
    """Status check del proxy con información detallada"""
    primary_ok, replica_ok = await asyncio.gather(check_health(PRIMARY), check_health(REPLICA))
    
    return {
        "proxy": {
            "status": "running",
            "version": "1.0.0",
            "active_backend": _active,
            "health_check_interval": INTERVAL,
            "max_failures": MAX_FAILS
        },
        "backends": {
            "primary": {
                "url": PRIMARY,
                "healthy": primary_ok,
                "consecutive_failures": _fail_counts[PRIMARY],
                "status": "active" if _active == PRIMARY else "standby"
            },
            "replica": {
                "url": REPLICA,
                "healthy": replica_ok,
                "consecutive_failures": _fail_counts[REPLICA],
                "status": "active" if _active == REPLICA else "standby"
            }
        },
        "failover": {
            "enabled": True,
            "automatic": True,
            "total_failovers": sum(1 for _ in [PRIMARY, REPLICA] if _fail_counts[_] > 0)
        }
    }

@app.api_route("/api/campaigns/{full_path:path}", methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"])
async def proxy_any(full_path: str, request: Request):
    # reconstruir URL destino (el backend de campañas expone /campaigns/*)
    target_base = _active
    if full_path:
        target_url = f"{target_base}/campaigns/{full_path}"
    else:
        target_url = f"{target_base}/campaigns/"

    # preparar request de reenvío
    method = request.method
    headers = dict(request.headers)
    headers.pop("host", None)  # evitar problemas de host
    body: Optional[bytes] = await request.body()

    try:
        resp = await _client.request(method, target_url, content=body, headers=headers)
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers={k: v for k, v in resp.headers.items() if k.lower() not in ("content-length", "transfer-encoding", "connection")}
        )
    except httpx.RequestError as e:
        return JSONResponse({"error": "upstream_unreachable", "detail": str(e), "active_target": _active}, status_code=502)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
