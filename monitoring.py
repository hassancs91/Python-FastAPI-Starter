from datetime import datetime
import socket
import time
from typing import Optional, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import aiomysql

class DatabaseHandler:
    def __init__(self, connection_string: str, **kwargs):
        self.connection_string = connection_string
        self.kwargs = kwargs
        self.is_initialized = False

    async def initialize(self):
        raise NotImplementedError()

    async def log_request(self, request_details: Dict[str, Any]):
        raise NotImplementedError()

class MongoHandler(DatabaseHandler):
    def __init__(self, connection_string: str, db_name: str, collection_name: str):
        super().__init__(connection_string, db_name=db_name, collection_name=collection_name)
        self.client = None
        self.collection = None

    async def initialize(self):
        if not self.is_initialized:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.collection = self.client[self.kwargs['db_name']][self.kwargs['collection_name']]
            self.is_initialized = True

    async def log_request(self, request_details: Dict[str, Any]):
        try:
            await self.collection.insert_one(request_details)
        except Exception as e:
            print(f"Failed to log to MongoDB: {str(e)}")

class MySQLHandler(DatabaseHandler):
    def __init__(self, host: str, user: str, password: str, db: str, table_name: str, port: int = 3306):
        super().__init__("", table_name=table_name)
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.port = port

    async def initialize(self):
        if not self.is_initialized:
            self.pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.db,
                autocommit=True
            )
            self.is_initialized = True

    async def log_request(self, request_details: Dict[str, Any]):
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    query = f"""
                        INSERT INTO {self.kwargs['table_name']} 
                        (timestamp, method, url_path, full_url, client_ip, user_agent, 
                        hostname, route, response_time_ms, status_code)
                        VALUES 
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        request_details["timestamp"],
                        request_details["method"],
                        request_details["url_path"],
                        request_details["full_url"],
                        request_details["client_ip"],
                        request_details["user_agent"],
                        request_details["hostname"],
                        request_details["route"],
                        request_details["response_time_ms"],
                        request_details["status_code"]
                    )
                    await cursor.execute(query, values)
        except Exception as e:
            print(f"Failed to log to MySQL: {str(e)}")

class MonitoringMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        db_handler: DatabaseHandler,
        skip_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.db_handler = db_handler
        self.hostname = self._get_hostname()
        
        self.skip_paths = skip_paths or {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
            "/health",
            "/favicon.ico",
            "/private-docs"
        }

    def _get_hostname(self) -> str:
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.skip_paths:
            return await call_next(request)

        await self.db_handler.initialize()
        start_time = time.time()
        
        try:
            request_details = self._collect_request_details(request)
            response = await call_next(request)
            self._add_response_details(request_details, response, start_time)
            
            await self.db_handler.log_request(request_details)
            return response
            
        except Exception as e:
            raise

    def _collect_request_details(self, request: Request) -> Dict[str, Any]:
        details = {
            "timestamp": datetime.utcnow(),
            "method": request.method,
            "url_path": str(request.url.path),
            "full_url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "hostname": self.hostname,
        }

        try:
            details["route"] = request.scope.get("route").path if request.scope.get("route") else str(request.url.path)
        except Exception:
            details["route"] = str(request.url.path)

        return details

    def _add_response_details(self, details: Dict[str, Any], response, start_time: float):
        details.update({
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "status_code": response.status_code
        })