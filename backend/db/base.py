from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Every datetime column becomes timestamptz, every dict column becomes JSONB
    type_annotation_map = {
        datetime: DateTime(timezone=True),
        dict: JSONB,
    }