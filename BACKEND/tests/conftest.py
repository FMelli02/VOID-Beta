# tests/conftest.py

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 1. IMPORTACIONES CLAVE DE TU APLICACIÓN
# Asegurate de que estas rutas sean correctas según tu estructura.
from BACKEND.main import app
from BACKEND.database.database import get_db
from BACKEND.database.models import Base

# --- 2. CONFIGURACIÓN DE LA BASE DE DATOS DE PRUEBA ---
# Se usa una base de datos SQLite en memoria: es rapidísima y se borra sola al final.
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Requerido para SQLite
)

# Creamos una "fábrica" de sesiones de prueba que usaremos en las fixtures.
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# --- 3. FIXTURE PARA LA BASE DE DATOS (LA CANCHA LIMPIA) ---
@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Esta fixture maneja la base de datos para CADA test:
    1. Crea todas las tablas antes de que el test empiece.
    2. Provee (con 'yield') una sesión limpia para que el test la use si necesita preparar datos.
    3. Borra todas las tablas cuando el test termina, sin dejar basura.
    """
    # Se conecta al motor de la BD de prueba
    async with test_engine.begin() as conn:
        # Crea todas las tablas definidas en tus modelos (los que heredan de Base)
        await conn.run_sync(Base.metadata.create_all)

    # Crea una sesión de prueba para ser usada en el test
    async with TestingSessionLocal() as session:
        # 'yield' es como una pausa: le pasa la sesión al test que la pidió.
        yield session

    # Cuando el test termina, el código continúa desde acá.
    async with test_engine.begin() as conn:
        # Borra todas las tablas para el siguiente test.
        await conn.run_sync(Base.metadata.drop_all)

# --- 4. FIXTURE PARA EL CLIENTE HTTP (PARA LLAMAR A TU API) ---
@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Esta fixture prepara tu aplicación FastAPI para ser testeada.
    Depende de `db_session` para asegurar que la base de datos esté lista primero.
    """
    # Función que vamos a usar para reemplazar la dependencia `get_db` original.
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # Aplicamos el "engaño": cuando la app pida la base de datos, le damos la de prueba.
    app.dependency_overrides[get_db] = override_get_db

    # Creamos un cliente HTTP que "habla" con tu app en memoria, sin levantar un servidor real.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Al final del test, limpiamos el engaño para no afectar a otros tests.
    app.dependency_overrides.clear()