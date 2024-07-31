# src/repoai/utils/tool_functions.py

import requests
from datetime import datetime
from zoneinfo import ZoneInfo

def get_current_time(timezone: str = "UTC") -> dict:
    try:
        current_time = datetime.now(ZoneInfo(timezone))
        return {
            "current_time": current_time.isoformat(),
            "timezone": timezone
        }
    except Exception as e:
        return {"error": f"Unable to get time for timezone {timezone}: {str(e)}"}