from typing import Union
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    # DRF authentication class that skips the CSRF test
    def enforce_csrf(self, request):
        return  # pragma: no cover

# ---------- generic helpers ----------

def validate_string(value: Union[str, None]) -> bool:
    # Return True when value is a non-empty (trimmed) string
    return isinstance(value, str) and bool(value.strip())

def time_to_seconds(time_str: str) -> float:

    # "12:34.56" → 754.56   or   "754.56" → 754.56
    if "." in time_str and ":" not in time_str:
        return float(time_str)
    minutes, seconds = map(float, time_str.split(":"))
    return round(minutes * 60 + seconds, 2)

def seconds_to_time(seconds: float) -> str:
    # 754.56 → '12:34.56' (mm:ss.xx)
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes}:{seconds:05.2f}"
