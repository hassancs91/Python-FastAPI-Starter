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


from middleware import APIKeyMiddleware


from database.mongo import establish_connection, mongo_db_instance
from database.mysql_main_db import init_db


from monitoring import MongoHandler, MonitoringMiddleware
from utils.logger_setup import initialize_logger, MongoLogConfig
from utils.config_loader import ENVIRONMENT, MONGO_CONNECTION_STRING
from utils.config_loader import API_KEY_HEADER_NAME



from routers import (
    sample
)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code (previously @app.on_event("startup"))
    print("Starting up...")
    

    #### Establish Mongo DB Connection ####

    #await establish_connection()

    #### Establish Mongo DB Connection ####


    #### Initialize logger with your database

    # Configure your collection names
    #mongo_config = MongoLogConfig(
    #     info_collection="info",
    #     warning_collection="warning",
    #     error_collection="error"
    # )
    # mongo_logger_db_name = "logs_db"
    # await initialize_logger(db_name=mongo_logger_db_name, mongo_config=mongo_config)

    #### Initialize logger with your database

    yield

    # Shutdown code
    print("Shutting down...")

    await mongo_db_instance.close()
    

   

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

#add the authentication middleware
app.add_middleware(APIKeyMiddleware)


#### Add API monitoring

# mongo_handler = MongoHandler(
#     connection_string=MONGO_CONNECTION_STRING,
#     db_name="pk_api_monitor",
#     collection_name="data"
# )

# app.add_middleware(MonitoringMiddleware, db_handler=mongo_handler)

#### Add API monitoring


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





#add new routers
app.include_router(sample.router, tags=["Sample"])




@app.get("/health-check")
async def read_health():
    try:
        return JSONResponse(
            status_code=200, content={"status": "healthy"}
        )
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






