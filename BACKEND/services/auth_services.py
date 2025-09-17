# En backend/services/auth_service.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pymongo.database import Database

from database.database import get_db_nosql
from utils import security
from schemas import user_schemas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Database = Depends(get_db_nosql)) -> user_schemas.UserOut:
    # ... (acá va la lógica para decodificar el token y buscar el usuario)
    # ... (esta es la que te di de ejemplo para la ruta /me)
    # ... la vamos a hacer bien ahora
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    # Convert ObjectId to string for Pydantic validation
    if "_id" in user:
        user["_id"] = str(user["_id"])

    return user_schemas.UserOut(**user)

async def get_current_admin_user(current_user: user_schemas.UserOut = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    return current_user