from fastapi import Header, HTTPException

from core.config import settings


async def verify_api_key(x_engine_key: str = Header(...)):
    if x_engine_key != settings.engine_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
