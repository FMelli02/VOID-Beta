# En backend/routers/products_router.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from schemas import product_schemas
from database.database import get_db
from database.models import Producto

router = APIRouter(
    prefix="/api/products",
    tags=["Products"]
)

@router.get("/", response_model=List[product_schemas.Product])
async def get_products(
    db: AsyncSession = Depends(get_db),
    material: Optional[str] = Query(None, description="Filtrar por material del producto"),
    precio_max: Optional[float] = Query(None, alias="precio", description="Filtrar por precio máximo"),
    categoria_id: Optional[int] = Query(None, description="Filtrar por ID de categoría"),
    talle: Optional[str] = Query(None, description="Filtrar por talle del producto"),
    color: Optional[str] = Query(None, description="Filtrar por color del producto"),
    skip: int = Query(0, ge=0, description="Número de productos a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número de productos a devolver"),
    sort_by: Optional[str] = Query(None, description="Ordenar por campo (ej: 'precio_asc', 'precio_desc', 'nombre_asc')")
):
    """
    Obtiene una lista de todos los productos, con filtros, paginación y ordenamiento.
    """
    query = select(Producto)
    
    # Filtros
    if material:
        query = query.where(Producto.material.ilike(f"%{material}%"))
    if precio_max:
        query = query.where(Producto.precio <= precio_max)
    if categoria_id:
        query = query.where(Producto.categoria_id == categoria_id)
    if talle:
        query = query.where(Producto.talle.ilike(f"%{talle}%"))
    if color:
        query = query.where(Producto.color.ilike(f"%{color}%"))
    
    # Ordenamiento
    if sort_by:
        if sort_by == "precio_asc":
            query = query.order_by(Producto.precio.asc())
        elif sort_by == "precio_desc":
            query = query.order_by(Producto.precio.desc())
        elif sort_by == "nombre_asc":
            query = query.order_by(Producto.nombre.asc())
        elif sort_by == "nombre_desc":
            query = query.order_by(Producto.nombre.desc())

    # Paginación
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products


@router.get("/{product_id}", response_model=product_schemas.Product)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el detalle de un solo producto por su ID.
    """
    result = await db.execute(select(Producto).filter(Producto.id == product_id))
    product = result.scalars().first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    return product
