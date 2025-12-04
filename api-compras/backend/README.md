# API Compras - FastAPI Backend

API de compras integrada con Stock y Logística vía gateway.

## Configuración

### Variables de Entorno

Copia `.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```

### Ejecutar con Docker Compose

```bash
cd backend
docker-compose up --build
```

La API estará disponible en: `http://localhost:5001`

## Endpoints Principales

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Iniciar sesión

### Productos (Proxy a Stock API)
- `GET /api/products` - Listar productos
- `GET /api/products/{id}` - Obtener producto

### Carrito
- `GET /api/cart` - Ver carrito
- `POST /api/cart` - Agregar al carrito
- `PUT /api/cart` - Actualizar cantidad
- `DELETE /api/cart/{product_id}` - Remover producto

### Órdenes
- `POST /api/orders/checkout` - Crear orden (integra Stock + Logística)
- `GET /api/orders` - Ver historial de órdenes

## Integración

### Stock API
- URL: `http://gateway:80/stock`
- Autenticación: Keycloak (grupo-08)
- Endpoints: `/productos`, `/reservas`

### Logística API
- URL: `http://gateway:80/logistica`
- Autenticación: Keycloak (grupo-08)
- Endpoints: `/shipping`, `/shipping/cost`

## Base de Datos

PostgreSQL 15 con las siguientes tablas:
- `users` - Usuarios locales
- `carts` - Carritos de compra
- `cart_items` - Items del carrito
- `orders` - Órdenes
- `products` - Snapshot de productos

## Desarrollo

### Migraciones

```bash
# Crear migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head
```

### Ejecutar localmente (sin Docker)

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 81
```

## Documentación API

Swagger UI: `http://localhost:5001/docs`
ReDoc: `http://localhost:5001/redoc`
