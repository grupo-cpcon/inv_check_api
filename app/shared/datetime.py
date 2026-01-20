from datetime import datetime
from zoneinfo import ZoneInfo
import os

TIMEZONE = ZoneInfo(os.getenv("APP_TIMEZONE"))

def time_now() -> datetime:
    return datetime.now(TIMEZONE)