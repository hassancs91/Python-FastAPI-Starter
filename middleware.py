from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import Request
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from utils.config_loader import ENVIRONMENT,API_KEY_HEADER_NAME, API_KEY_PASSPHRASE


WHITELISTED_PATHS = ["/pdocs", "/openapi.json", "/health-check", "/"]


api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=True)


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check if running in development mode
        if ENVIRONMENT == 'dev':
            return await call_next(request)
        
        if request.url.path not in WHITELISTED_PATHS:
            api_key = request.headers.get(API_KEY_HEADER_NAME)
            if api_key != API_KEY_PASSPHRASE:
                return JSONResponse(
                    status_code=401, content={"detail": "Invalid API key"}
                )
        return await call_next(request)
