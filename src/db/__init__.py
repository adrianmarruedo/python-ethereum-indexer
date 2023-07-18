from __future__ import annotations

from sqlalchemy.orm import declarative_base

from .db_utils import DBSession

Base = declarative_base()
engine = DBSession.get_engine()
Session = DBSession.get_db()

from .schemas import *
