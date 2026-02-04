from datetime import datetime
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv

load_dotenv() 

TIMEZONE = ZoneInfo(os.getenv("APP_TIMEZONE"))

def time_now() -> datetime:
    return datetime.now(TIMEZONE)