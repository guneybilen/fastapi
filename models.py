import datetime as _dt

import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import passlib.hash as _hash

import database as _database


class User(_database.Base):
    __tablename__ = "users"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    full_name = _sql.Column(_sql.String)
    disabled = _sql.Column(_sql.Boolean)
    username = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String, unique=True, index=True)
    hashed_password = _sql.Column(_sql.String)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)

    items = _orm.relationship("Item", back_populates="item")

    def verify_password(self, password: str):
        return _hash.bcrypt.verify(password, self.hashed_password)


class Item(_database.Base):
    __tablename__ = "items"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.Integer, _sql.ForeignKey("users.id"))
    item_text = _sql.Column(_sql.String, index=True)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    item_images_names = _sql.Column(_sql.String, default=None)

    item = _orm.relationship("User", back_populates="items")


class Token(_database.Base):
    __tablename__ = "tokens"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    access_token = _sql.Column(_sql.String, default=None)
    token_type = _sql.Column(_sql.String, default=None)


class TokenData(_database.Base):
    __tablename__ = "tokendatas"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    username = _sql.Column(_sql.String, default=None)
