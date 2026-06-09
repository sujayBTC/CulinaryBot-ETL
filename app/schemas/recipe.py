from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class RecipeBase(BaseModel):
    recipe_category: str
    name: str
    ingredients: list
    method: list
    meta_data: dict
    video_url: str
    image_url: str
    created_by_id: int | None = None
    updated_by_id: int | None = None
    recipe_form_id: int | None = None
    model_config: ConfigDict = {"use_enum_values": True, "from_attributes": True}


class RecipeMetaDataSchema(BaseModel):
    metadata: str | None = None
    description: str | None = None
    protein_type: str | None = None
    category_time_of_day: str | None = None


class RecipeShortlist(BaseModel):
    id: int
    name: str
    ingredients: list
    meta_data: RecipeMetaDataSchema
    image_url: str


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(BaseModel):
    recipe_category: str | None = None
    name: str | None = None
    ingredients: dict | None = None
    method: dict | None = None
    meta_data: dict | None = None
    video_url: str | None = None
    image_url: str | None = None


class Recipe(RecipeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "recipe_category": self.recipe_category,
            "name": self.name,
            "ingredients": self.ingredients,
            "method": self.method,
            "meta_data": self.meta_data,
            "video_url": self.video_url,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_by_id": str(self.created_by_id) if self.created_by_id else None,
            "updated_by_id": str(self.updated_by_id) if self.updated_by_id else None,
            "recipe_form_id": str(self.recipe_form_id) if self.recipe_form_id else None,
        }
