# En BACKEND/database/database.py

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from motor.motor_asyncio import AsyncIOMotorClient

# Carga las variables del archivo .env
load_dotenv()

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS SQL (MySQL) ---
DB_SQL_USER = os.getenv("DB_SQL_USER")
DB_SQL_PASS = os.getenv("DB_SQL_PASS")
DB_SQL_HOST = os.getenv("DB_SQL_HOST")
DB_SQL_NAME = os.getenv("DB_SQL_NAME")

DATABASE_URL = f"mysql+aiomysql://{DB_SQL_USER}:{DB_SQL_PASS}@{DB_SQL_HOST}/{DB_SQL_NAME}"

# El engine es necesario para el lifespan en main.py y para el chequeo
engine = create_async_engine(DATABASE_URL)

# Creamos un sessionmaker asíncrono
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependencia para obtener una sesión de base de datos asíncrona
async def get_db() -> AsyncSession: # type: ignore
    async with AsyncSessionLocal() as session:
        yield session

async def check_sql_connection():
    """Verifica la conexión con la base de datos MySQL."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"database": "MySQL", "status": "ok", "message": "Conexión exitosa."}
    except Exception as e:
        return {"database": "MySQL", "status": "error", "message": str(e)}

# --- CONFIGURACIÓN DE LA BASE DE DATOS NoSQL (MongoDB) ---
MONGO_URI = os.getenv("DB_NOSQL_URI")
MONGO_DB_NAME = os.getenv("DB_NOSQL_NAME") # <-- Asegurate de tener esta variable en .env

client = AsyncIOMotorClient(MONGO_URI)
db_nosql = client[MONGO_DB_NAME]

# Dependencia para la base de datos NoSQL que usarán tus routers
async def get_db_nosql():
    yield db_nosql

async def check_nosql_connection():
    """Verifica la conexión con la base de datos MongoDB."""
    try:
        # El comando 'ping' es la forma estándar de verificar la conexión en Mongo
        await client.admin.command('ping')
        return {"database": "MongoDB", "status": "ok", "message": "Conexión exitosa."}
    except Exception as e:
        return {"database": "MongoDB", "status": "error", "message": str(e)}