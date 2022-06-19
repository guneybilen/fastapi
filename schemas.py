import datetime as _dt

from pydantic import BaseModel


class _UserBase(BaseModel):
    email: str | None = None


class UserInDB(_UserBase):
    hashed_password: str

    class Config:
        orm_mode = True


class User(_UserBase):
    id: int
    date_created: _dt.datetime
    full_name: str | None = None
    disabled: bool | None = None
    username: str

    class Config:
        orm_mode = True


class _ItemBase(BaseModel):
    item_text: str


class ItemCreate(_ItemBase):
    pass


class Item(_ItemBase):
    id: int
    user_id: int
    item_images_names: list
    date_created: _dt.datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    id: int
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: int
    username: str | None = None
