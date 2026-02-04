from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from dataclasses import dataclass, field
import datetime
from bson import ObjectId
import datetime
from app.modules.report.report_choices import HierarchyStandChoice, ImageExportModeChoice


class CreateInventoryResponsibilityAgreementReportRequest(BaseModel):
    parent_location_ids: List[str]
    
class CreateAnalyticalReportRequest(BaseModel):
    parent_ids: List[str]

class ImagesExportRequest(BaseModel):
    mode: ImageExportModeChoice
    parent_id: Optional[str] = None

@dataclass
class InventoryResposabilityAgreementItemDTO:
    reference: str
    is_app_created: bool
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
    level: int
    hierarchy_stand: HierarchyStandChoice
    is_app_created: Optional[bool] = False
    reference: Optional[str] = None
    checked: Optional[bool] = False
    checked_at: Optional[datetime.datetime] = None
    asset_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    location_path: Optional[List[str]] = field(default_factory=list)
    hierarchy_path: Optional[List[str]] = field(default_factory=list)