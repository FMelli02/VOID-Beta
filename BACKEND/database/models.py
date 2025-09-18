from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DECIMAL,
    TIMESTAMP,
    ForeignKey,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy import Date # Asegurate de importar Date
# Esta es la "mesa de dibujo" sobre la que creamos nuestros planos (modelos)
Base = declarative_base()


class Categoria(Base):
    """
    Representa la tabla 'categorias' en la base de datos.
    Cada producto pertenece a una de estas categorías.
    """
    # El nombre que tendrá la tabla en la base de datos
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False, index=True)

    # La relación: Le dice a SQLAlchemy que una Categoría puede tener muchos Productos.
    # El 'back_populates' es para que la relación funcione en ambos sentidos.
    productos = relationship("Producto", back_populates="categoria")


class Producto(Base):
    """
    Representa la tabla 'productos' en la base de datos.
    Contiene toda la información de cada producto de la tienda.
    """
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(DECIMAL(10, 2), nullable=False)
    sku = Column(String(100), unique=True, nullable=False)
    url = Column(String(100), unique=True, nullable=False)
    
    # La clave foránea: Conecta este producto con una fila de la tabla 'categorias'
    material = Column(String(100), nullable=True) # Agregamos el material del producto
    talle = Column(String(50), nullable=True) # Nuevo campo para el talle
    color = Column(String(50), nullable=True) # Nuevo campo para el color
    stock = Column(Integer, nullable=False, default=0) # Nuevo campo para el stock

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    
    # La relación inversa: Le dice a SQLAlchemy que un Producto tiene una Categoría.
    categoria = relationship("Categoria", back_populates="productos")

    # Campos de fecha automáticos
    creado_en = Column(TIMESTAMP, server_default=func.now())
    actualizado_en = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    # Adentro de tu archivo backend/database/models.py


class Gasto(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String(255), nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    categoria = Column(String(100), nullable=True)
    fecha = Column(Date, nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())

class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True)
    total = Column(DECIMAL(10, 2), nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())
    productos = relationship("OrdenProducto", back_populates="orden")

class OrdenProducto(Base):
    __tablename__ = "orden_productos"

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, nullable=False)

    orden = relationship("Orden", back_populates="productos")
    producto = relationship("Producto")

class ConversacionIA(Base):
    __tablename__ = "conversaciones_ia"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(String(255), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    respuesta = Column(Text, nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())