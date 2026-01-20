from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from pydantic import BaseModel
from dataclasses import dataclass, field
import datetime

class CreateAnalyticalReportRequest(BaseModel):
    parent_ids: List[str]
    
@dataclass
class ItemNodeDTO:
    _id: str
    name: str
    node_type: str
    is_checked: bool = False
    checked_at: Optional[datetime] = None
    photos: List[str] = field(default_factory=list)
    children: List["ItemNodeDTO"] = field(default_factory=list)