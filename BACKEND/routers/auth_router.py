# En backend/routers/auth_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.database import Database
from datetime import datetime

from schemas import user_schemas
from utils import security
from database.database import get_db_nosql
# Importamos el servicio para obtener el usuario actual
from services import auth_services as auth_service

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=user_schemas.UserOut)
async def register_user(user: user_schemas.UserCreate, db: Database = Depends(get_db_nosql)):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El email ya está registrado."
        )

    hashed_password = security.get_password_hash(user.password)
    
    # Preparamos el documento del usuario para guardar en MongoDB
    user_document = user.model_dump()
    user_document["hashed_password"] = hashed_password
    del user_document["password"]
    
    user_document["role"] = "user" 
    user_document["created_at"] = datetime.now()

    # NOTE: This is a simple way to create an admin user for development.
    # For production, consider a more secure method like a CLI command.
    if user.email == "voidindumentaria.mza@gmail.com":
        user_document["role"] = "admin"

    result = await db.users.insert_one(user_document)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    return user_schemas.UserOut(**created_user)

@router.post("/login", response_model=user_schemas.Token)
async def login_for_access_token(db: Database = Depends(get_db_nosql), form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"email": form_data.username})
    
    if not user or not security.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # <-- CAMBIO: Incluimos el rol en los datos del token
    token_data = {
        "sub": user["email"], 
        "user_id": str(user["_id"]),
        "role": user.get("role", "user") # Usamos .get por si un usuario viejo no tiene rol
    }
    
    access_token = security.create_access_token(data=token_data)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=user_schemas.UserOut, summary="Obtener datos del usuario actual")
async def read_users_me(current_user: user_schemas.UserOut = Depends(auth_service.get_current_user)):
    """
    Un endpoint protegido. Solo funciona si mandás un token JWT válido.
    Te devuelve los datos del usuario dueño del token.
    """
    return current_user