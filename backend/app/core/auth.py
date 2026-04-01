from fastapi import Depends, HTTPException, Request
from app.config import REQUIRE_AUTH, API_KEYS

def verify_api_key(request: Request = None):
    if not REQUIRE_AUTH:
        return "no-auth"
    
    # Dummy implementation
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return API_KEYS[api_key]