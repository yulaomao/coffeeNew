from datetime import datetime, timezone
import time
from typing import Optional

def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)

def utc_timestamp() -> float:
    """Get current UTC timestamp"""
    return time.time()

def iso_format(dt: datetime) -> str:
    """Format datetime to ISO8601 string"""
    return dt.isoformat()

def parse_iso(iso_string: str) -> Optional[datetime]:
    """Parse ISO8601 string to datetime"""
    try:
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

def format_duration(seconds: int) -> str:
    """Format seconds to human readable duration"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}小时{minutes}分钟"
        return f"{hours}小时"

def seconds_until(target_time: datetime) -> int:
    """Get seconds until target time"""
    now = utc_now()
    if target_time <= now:
        return 0
    return int((target_time - now).total_seconds())