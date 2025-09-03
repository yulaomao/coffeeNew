from datetime import datetime, timezone
import pytz


def utc_now():
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def parse_iso_datetime(iso_string):
    """Parse ISO 8601 datetime string to UTC datetime"""
    if not iso_string:
        return None
    
    try:
        # Handle various ISO formats
        if iso_string.endswith('Z'):
            # UTC format with Z
            return datetime.fromisoformat(iso_string[:-1]).replace(tzinfo=timezone.utc)
        elif '+' in iso_string or iso_string.count('-') > 2:
            # Timezone aware format
            return datetime.fromisoformat(iso_string)
        else:
            # Assume UTC if no timezone info
            return datetime.fromisoformat(iso_string).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def to_iso_string(dt):
    """Convert datetime to ISO 8601 string"""
    if not dt:
        return None
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()


def format_duration(seconds):
    """Format duration in seconds to human readable string"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"