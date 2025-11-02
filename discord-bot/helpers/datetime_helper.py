from datetime import datetime, timezone, timedelta

def get_timeout_seconds(end_dt: datetime):
    now_dt = datetime.now(timezone.utc)
    timeout_seconds = (end_dt - now_dt).total_seconds()
    return timeout_seconds

def to_unix(dt: datetime) -> int:
    """Convert a datetime to a Unix timestamp (seconds)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return int(dt.timestamp())


def convert_datetime(dt: datetime, style: str = "f") -> str:
    """
    Convert a datetime to a Discord timestamp format.
    Common style codes:
      t = short time
      T = long time
      d = short date
      D = long date
      f = short date/time
      F = long date/time
      R = relative time (e.g. 'in 5 minutes')
    """
    return f"<t:{to_unix(dt)}:{style}>"


def parse_duration_string(time_str: str) -> datetime:
    """
    Convert a relative duration string like '5m', '2h', '1d', or '30s'
    into a future UTC datetime.
    """
    now = datetime.now(timezone.utc)
    unit = time_str[-1]
    value = int(time_str[:-1])
    
    if unit == 'm':
        delta = timedelta(minutes=value)
    elif unit == 'h':
        delta = timedelta(hours=value)
    elif unit == 'd':
        delta = timedelta(days=value)
    elif unit == 's':
        delta = timedelta(seconds=value)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")
    
    return now + delta
