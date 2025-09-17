import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from BACKEND.database.models import Producto, Categoria

@pytest.mark.asyncio
async def test_get_products_empty(client: AsyncClient):
    """Prueba que se obtiene una lista vacía si no hay productos."""
    response = await client.get("/api/products/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_products_with_data(client: AsyncClient, db_session: AsyncSession):
    """Prueba que se obtienen los productos que existen en la BD."""
    # Crear categoría primero (requerida por FK)
    categoria = Categoria(nombre="Ropa")
    db_session.add(categoria)
    await db_session.commit()
    await db_session.refresh(categoria)

    # Insertar productos con categoria_id válido
    db_session.add_all([
        Producto(nombre="Camiseta Test", precio=100.0, stock=10, categoria_id=categoria.id, sku="SKU-CAM-TEST"),
        Producto(nombre="Pantalón Test", precio=200.0, stock=5, categoria_id=categoria.id, sku="SKU-PAN-TEST"),
    ])
    await db_session.commit()

    response = await client.get("/api/products/")
    assert response.status_code == 200
    data = response.json()

    # Chequear que al menos los 2 que insertamos están en la respuesta
    nombres = [p["nombre"] for p in data]
    assert "Camiseta Test" in nombres
    assert "Pantalón Test" in nombres

@pytest.mark.asyncio
async def test_get_single_product_found(client: AsyncClient, db_session: AsyncSession):
    """Prueba que se puede obtener un solo producto por su ID."""
    categoria = Categoria(nombre="Accesorios")
    db_session.add(categoria)
    await db_session.commit()
    await db_session.refresh(categoria)

    producto_unico = Producto(
        nombre="Producto Único", precio=150.0, stock=3, categoria_id=categoria.id, sku="SKU-UNICO-1"
    )
    db_session.add(producto_unico)
    await db_session.commit()
    await db_session.refresh(producto_unico)

    response = await client.get(f"/api/products/{producto_unico.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == "Producto Único"
    assert data["id"] == producto_unico.id

@pytest.mark.asyncio
async def test_get_single_product_not_found(client: AsyncClient):
    """Prueba que se obtiene un error 404 si el producto no existe."""
    response = await client.get("/api/products/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Producto no encontrado"}
