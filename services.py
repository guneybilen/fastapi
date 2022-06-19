import os as _os
import shutil
import time as _time
from pathlib import Path
from tempfile import NamedTemporaryFile

import jose as _jose
import sqlalchemy.orm as _orm
from dotenv import load_dotenv

import auth_api as _auth_api
import fastapi as _fastapi
import models as _models
import schemas as _schemas
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm


load_dotenv()  # take environment variables from .env.


app = FastAPI()


async def create_token(user: _models.User):
    user_obj = _schemas.User.from_orm(user)

    user_dict = user_obj.dict()
    del user_dict["date_created"]

    token = _jose.jwt.encode(user_dict, _os.getenv("SECRET"))

    return dict(access_token=token, token_type="bearer")


async def create_item(user: _schemas.User, db: _orm.Session, item: _schemas.ItemCreate):
    item = _models.Item(**item.dict(), user_id=user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _schemas.Item.from_orm(item)


async def get_user_items(user: _schemas.User, db: _orm.Session):
    items = db.query(_models.Item).filter_by(user_id=user.id)

    return list(map(_schemas.Item.from_orm, items))


def iter_file(file):
    with open(f"{file}", mode="rb") as file_like:
        yield from file_like


async def save_upload_file(user: _schemas.User, db: _orm.Session, destination: str, upload_file: _fastapi.UploadFile):
    try:
        print("hello")
        await handle_upload_file(user.email, upload_file, destination)
        user = await _auth_api.get_user_by_email(email=user.email, db=db)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # item = _models.Item(user_id=user.id)
        #
        # item_data = item.dict(exclude_unset=True)
        # # for key, value in user.items():
        # item_data['item_data.item_images_names'].push(returned_file)
        #
        # db.add(item_data)
        # db.commit()
        # db.refresh(item_data)
        # return _schemas.Item.from_orm(item_data)
        return None
    except HTTPException as e:
        print(f"{e}")
    finally:
        upload_file.file.close()


async def save_upload_file_tmp(username: str, upload_file: _fastapi.UploadFile, destination: str):
    try:
        suffix = Path(upload_file.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)
            if not _os.path.exists(f"{destination}/{username}"):
                _os.mkdir(f"{destination}/{username}")
            shutil.copy(
                tmp_path, f"{destination}/{username}/{upload_file.filename}")
            print("File copied successfully.")
            if _os.path.exists(tmp.name):
                _os.remove(tmp.name)
            return upload_file.filename

    # If source and destination are same
    except shutil.SameFileError:
        print("Source and destination represents the same file.")

    # If there is any permission issue
    except PermissionError:
        print("Permission denied.")

    # For other errors
    except HTTPException as e:
        print(f"Error occurred while copying file... /n {e}")
    finally:
        upload_file.file.close()


async def handle_upload_file(username: str, upload_file: _fastapi.UploadFile, destination: str):
    return await save_upload_file_tmp(username, upload_file, destination)


@app.get("/api/users/me/", response_model=_schemas.User)
async def read_users_me(current_user: _schemas.User = Depends(_auth_api.get_current_active_user)):
    return current_user


@app.get("/api/users/me/items/")
async def read_own_items(current_user: _schemas.User = Depends(_auth_api.get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]


@app.post("/api/token", response_model=_schemas.Token)
async def login_for_access_token(db, form_data: OAuth2PasswordRequestForm = Depends()):
    user = _auth_api.authenticate_user(
        db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = _time.timedelta(
        minutes=_os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    access_token = _auth_api.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
