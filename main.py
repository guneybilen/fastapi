from typing import List
import fastapi as _fastapi
import fastapi.security as _security

import sqlalchemy.orm as _orm
import os as _os
import services as _services
import schemas as _schemas
import database as _database
import auth_api as _auth_api

app = _fastapi.FastAPI()

if not _os.path.exists('database.db'):
    _database.Base.metadata.create_all(bind=_database.engine)


@app.post("/api/users")
async def create_user(user: _schemas.User, db: _orm.Session = _fastapi.Depends(_auth_api.get_db)):
    db_user = await _services.get_user_by_email(email=user.email, db=db)
    if db_user:
        raise _fastapi.HTTPException(
            status_code=400,
            detail="User with that email already exists")

    user = await _services.create_user(user=user, db=db)

    return await _services.create_token(user=user)


@app.post("/api/token")
async def generate_token(form_data: _security.OAuth2PasswordRequestForm = _fastapi.Depends(),
                         db: _orm.Session = _fastapi.Depends(_auth_api.get_db)):
    user = await _services.authenticate_user(email=form_data.username, password=form_data.password, db=db)

    if not user:
        raise _fastapi.HTTPException(
            status_code=401, detail="Invalid Credentials")

    return await _services.create_token(user=user)


@app.get("/api/users/me", response_model=_schemas.User)
async def get_user(user: _schemas.User = _fastapi.Depends(_auth_api.get_current_user)):
    return user


@app.post("/api/userItems", response_model=_schemas.Item)
async def create_item(
        item: _schemas.ItemCreate,
        user: _schemas.User = _fastapi.Depends(_auth_api.get_current_user),
        db: _orm.Session = _fastapi.Depends(_auth_api.get_db)
):
    return await _services.create_item(user=user, db=db, item=item)


@app.get("/api/items", response_model=List[_schemas.Item])
async def get_user_items(user: _schemas.User = _fastapi.Depends(_auth_api.get_current_user),
                         db: _orm.Session = _fastapi.Depends(_auth_api.get_db)):
    return await _services.get_user_items(user=user, db=db)


@app.post('/api/images')
async def post_user_images(user: _schemas.User = _fastapi.Depends(_auth_api.get_current_user),
                           db: _orm.Session = _fastapi.Depends(
                               _auth_api.get_db),
                           upload_file: _fastapi.UploadFile = _fastapi.File(...), destination: str = "images"):
    return await _services.save_upload_file(user=user, db=db, upload_file=upload_file, destination=destination)
