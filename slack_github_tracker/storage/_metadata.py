from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

metadata = MetaData()


class Base(MappedAsDataclass, DeclarativeBase):
    metadata = metadata
