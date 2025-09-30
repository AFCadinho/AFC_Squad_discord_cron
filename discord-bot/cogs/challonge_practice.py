import os

CH_BASE = "https://api.challonge.com/v1"

CH_USER = os.getenv("CHALLONGE_USERNAME", "")
CH_KEY  = os.getenv("CHALLONGE_API_KEY", "")

def _auth():
    if not CH_USER or not CH_KEY:
        raise RuntimeError("Set CHALLONGE_USERNAME and CHALLONGE_API_KEY in your .env")
    return (CH_USER, CH_KEY)