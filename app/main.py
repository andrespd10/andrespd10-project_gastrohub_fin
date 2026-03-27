from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import time

from app.api.auth import router as auth_router
from app.api.routes.usuarios import router as usuarios_router
from app.api.routes.productos import router as productos_router
from app.api.routes.mesas import router as mesas_router
from app.api.routes.pedidos import router as pedidos_router
from app.api.routes.detalle_pedido import router as detalles_router
from app.api.routes.pagos import router as pagos_router


# --- IMPORTACIONES PARA LA BASE DE DATOS (Líneas 7-10) ---
from app.db.base import Base
from app.db.session import engine
# Importamos el archivo models.py que está dentro de la carpeta models
import app.models.models as models

# Esta línea ejecuta la creación física de las tablas en MySQL
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GastroHub API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limit en memoria simple (por IP)
RATE_LIMIT = 60
WINDOW_SECONDS = 60
_limit_store = {}


def rate_limiter(client_ip: str):
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=WINDOW_SECONDS)
    hits = _limit_store.get(client_ip, [])
    hits = [h for h in hits if h > window_start]
    hits.append(now)
    _limit_store[client_ip] = hits
    if len(hits) > RATE_LIMIT:
        return False
    return True


@app.middleware("http")
async def limit_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Límite de peticiones excedido"},
        )

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(productos_router)
app.include_router(mesas_router)
app.include_router(pedidos_router)
app.include_router(detalles_router)
app.include_router(pagos_router)
