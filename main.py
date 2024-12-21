from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException


from starlette.applications import Starlette
from starlette.requests import Request

#####imports from your other modules


#from .monitoring import MonitoringMiddleware
#from .utils.dependencies import get_logger

#from .database.mongo import get_database
#from .utils.config_loader import MONGO_CONNECTION_STRING

from routers import (
    test
)

from database.mongo import establish_connection, mongo_db_instance
from database.mysql_main_db import engine as mainSQLDbEngine, init_db as initMySQLEngine

from utils.logger_setup import initialize_logger, MongoLogConfig
from utils.logger_setup import get_logger
from utils.config_loader import ENVIRONMENT
from middleware import APIKeyMiddleware
from utils.config_loader import API_KEY_HEADER_NAME, API_KEY_PASSPHRASE


#api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=True)


#logger = get_logger()



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code (previously @app.on_event("startup"))
    print("Starting up...")
    
    

    #await establish_connection()
    #await initMySQLEngine()

    # Initialize logger with your database name
    # Configure your collection names (optional)
    #mongo_config = MongoLogConfig(
    #     info_collection="info",
    #     warning_collection="warning",
    #     error_collection="error"
    # )
    # mongo_logger_db_name = "pk_logs_db"
    # await initialize_logger(db_name=mongo_logger_db_name, mongo_config=mongo_config)

    yield

    # Shutdown code
    print("Shutting down...")

    #await mongo_db_instance.close()
    #await mainSQLDbEngine.dispose()

   

app = FastAPI(
    title="API System",
    description="Private APIs",
    version="1.0.0",
    servers=[
        {"url": "https://api.YOURDOMAIN.com/", "description": "Production server"},
        {"url": "http://127.0.0.1:8000", "description": "Development server"},
    ],
    docs_url="/pdocs",
    lifespan=lifespan
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(APIKeyMiddleware)



original_openapi = app.openapi
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = original_openapi()
    
    # Initialize components if it doesn't exist
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
        
    openapi_schema["components"]["securitySchemes"] = {
        API_KEY_HEADER_NAME: {"type": "apiKey", "in": "header", "name": API_KEY_HEADER_NAME}
    }
    openapi_schema["security"] = [{API_KEY_HEADER_NAME: []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema
app.openapi = custom_openapi



@app.get("/")
def read_root():
    url = "https://YOURDOMAIN.com"
    return RedirectResponse(url=url)

@app.get("/health-check")
async def read_health():
    try:
      
        # Additional checks can go here
        return {"status": "healthy"}

    except Exception as ex:
        return JSONResponse(
            status_code=503, content={"status": "unhealthy", "details": str(ex)}
        )




@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    try:
        # logger.error(
        #    f"An HTTP error occurred: {exc.detail}",
        #    extra={"request_path": request.url.path},
        # )
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail},
        )
    except:
        return



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    try:
        # logger.error(
        #    f"An unexpected error occurred while processing path {request.url.path}: {exc}"
        # )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An unexpected error occurred",
                "result": None,
            },
        )
    except :
        return



#app.include_router(youtube.router, tags=["youtube"])
#app.include_router(email.router, tags=["email"])

