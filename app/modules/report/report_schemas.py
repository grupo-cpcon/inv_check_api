from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from dataclasses import dataclass, field
import datetime
from bson import ObjectId
import datetime

class CreateInventoryResponsabilityAgreementReportRequest(BaseModel):
    parent_location_ids: List[str]
    
class CreateAnalyticalReportRequest(BaseModel):
    parent_ids: List[str]

@dataclass
class InventoryResposabilityAgreementItemDTO:
    reference: str
    color: str
    checked: Optional[bool] = False
    description: Optional[str] = None
    serial: Optional[str] = None
    model: Optional[str] = None

    photo_key: Optional[str] = None
    photo_base64: Optional[str] = None
    parent_reference: Optional[str] = None

@dataclass
class InventoryResposabilityAgreementLocationDTO:
    reference: str
    level: int
    path: Optional[str] = None
    items: List[InventoryResposabilityAgreementItemDTO] = field(default_factory=list)

@dataclass
class AnalyticalReportRawDataDTO:
    _id: ObjectId
    reference: Optional[str] = None
    checked: Optional[bool] = None
    checked_at: Optional[datetime.datetime] = None
    path: Optional[List[str]] = None
    asset_data: Optional[Dict[str, Any]] = None