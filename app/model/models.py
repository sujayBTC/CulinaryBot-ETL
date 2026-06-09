from sqlalchemy import Column, String, BigInteger, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.model.base import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    recipe_category = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)

    ingredients = Column(JSONB, nullable=False)
    method = Column(JSONB, nullable=False)
    meta_data = Column(JSONB, nullable=True)

    video_url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.timezone("UTC", func.now()),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.timezone("UTC", func.now()),
        onupdate=func.timezone("UTC", func.now()),
    )

    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_by_id = Column(BigInteger, nullable=True)
    updated_by_id = Column(BigInteger, nullable=True)

    recipe_form_id = Column(BigInteger, unique=True, nullable=True)
