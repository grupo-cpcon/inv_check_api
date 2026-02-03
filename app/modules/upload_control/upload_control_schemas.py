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