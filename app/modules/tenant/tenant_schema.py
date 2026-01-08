from typing import List, Union

from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
import datetime

from app.core.db.py_object_id import PyObjectId


class TenantSchema(BaseModel):
    id:         ObjectId = Field(alias="_id")
    database:   str
    name:       str
    is_active:  bool = True
    created_at: datetime.datetime

    model_config = ConfigDict(
        arbitrary_types_allowed = True
    )


class TenantPartialDTO(BaseModel):
    name: str
    database: str
    note: str


class TenantResponseDTO(BaseModel):
    id:         PyObjectId = Field(alias="_id", serialization_alias="id")
    database:   str
    name:       str
    is_active:  bool = True
    created_at: datetime.datetime

    model_config = ConfigDict(
        populate_by_name=True
    )


class TenantListResponseDTO(BaseModel):
    total: int
    tenants: List[Union[TenantResponseDTO, TenantPartialDTO]]


class TenantCreateUpdateDTO(BaseModel):
    database:   str
    name:       str

