import os as _os
from datetime import datetime, timedelta

import sqlalchemy.orm as _orm
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

import database as _database
import fastapi as _fastapi
import models as _models
import schemas as _schemas
import passlib.hash as _hash
from validate_email import validate_email

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


load_dotenv()  # take environment variables from .env.


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_user(user: _schemas.User, db: _orm.Session):
    try:
        valid = validate_email(email=user.email)

        email = valid.email

        user_obj = _models.User(
            email=email, hashed_password=_hash.bcrypt.hash(user.password))

    except validate_email.EmailNotValidError:
        raise _fastapi.HTTPException(
            status_code=404, detail="Please enter a valid email")

    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db: _orm.Session, username: str):
    if username in db:
        user_dict = db[username]
        return _schemas.UserInDB(**user_dict)


async def get_user_by_email(email: str, db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(_models.User).filter(_models.User.email == email).first()


async def authenticate_user(email: str, password: str, db: _orm.Session = _fastapi.Depends(get_db)):
    user = await get_user_by_email(email=email, db=db)

    if not user:
        return False

    if not user.verify_password(password):
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, _os.getenv(
        "SECRET"), algorithm=_os.getenv("ALGORITHM"))
    return encoded_jwt


async def get_current_user(db: _orm.Session = _fastapi.Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _os.getenv("SECRET"),
                             algorithms=[_os.getenv("ALGORITHM")])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = _schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: _schemas.User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
