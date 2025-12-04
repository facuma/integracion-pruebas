from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.db import engine, Base
from app.models import carts as cart_item_model
from app.routers import cart, orders, products, stock_bridge, users, auth, debug
from app.routers import shipping as shipping_router
from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings


app = FastAPI(title="Backend Compras", version="1.0")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]


# (dev) crear tablas si aún no usás Alembic
Base.metadata.create_all(bind=engine)

# Montar archivos estáticos para imágenes de productos, /static -> ./app/uploads
Upload_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(Upload_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=Upload_DIR), name="static")

# Incluir routers
#app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
#app.include_router(product_router.router)
#app.include_router(product_image_router.router)
app.include_router(users.router)
app.include_router(shipping_router.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(stock_bridge.router)
app.include_router(products.router)
app.include_router(debug.router)  # Debug endpoints
app.include_router(auth.router)
#app.include_router(category_router.router)
#app.include_router(booking.router, prefix="/api/booking", tags=["Booking"])
#app.include_router(tracking.router, prefix="/api/tracking", tags=["Tracking"])


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def root():
    return {"message": "Backend Compras funcionando 🚀"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)