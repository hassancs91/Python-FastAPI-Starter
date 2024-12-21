import logging
from logging.handlers import TimedRotatingFileHandler
import os
import json
import sys
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class MongoLogConfig:
    """Configuration for MongoDB logging collections"""
    info_collection: str = "info"
    warning_collection: str = "warning"
    error_collection: str = "error"

    @property
    def collections(self):
        return {
            "info": self.info_collection,
            "warning": self.warning_collection,
            "error": self.error_collection
        }


class MongoDBHandler(logging.Handler):
    def __init__(self, db: AsyncIOMotorDatabase, collections: dict):
        super().__init__()
        self.db = db
        self.collections = collections
        self._queue = asyncio.Queue()
        self._task = None

    def _get_collection_name(self, level: int) -> str:
        """Determine collection name based on log level"""
        if level >= logging.ERROR:
            return self.collections["error"]
        elif level >= logging.WARNING:
            return self.collections["warning"]
        else:
            return self.collections["info"]

    async def _worker(self):
        while True:
            try:
                record = await self._queue.get()
                if record is None:  # Shutdown signal
                    break
                
                collection_name = self._get_collection_name(record['level_number'])
                collection = self.db[collection_name]
                await collection.insert_one(record)
            except Exception as e:
                print(f"Error writing to MongoDB: {e}", file=sys.stderr)
            finally:
                self._queue.task_done()

    def emit(self, record):
        try:
            log_entry = {
                "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "level_number": record.levelno,
                "message": record.getMessage(),
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line_number": record.lineno
            }
            
            if record.exc_info:
                log_entry["stack_trace"] = self.formatter.formatException(record.exc_info)

            asyncio.create_task(self._queue.put(log_entry))
        except Exception as e:
            print(f"Error formatting log for MongoDB: {e}", file=sys.stderr)

    async def start(self):
        """Start the background worker"""
        if self._task is None:
            self._task = asyncio.create_task(self._worker())

    async def stop(self):
        """Stop the background worker"""
        if self._task is not None:
            await self._queue.put(None)  # Send shutdown signal
            await self._task
            self._task = None


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage()
        }

        if record.exc_info:
            log_record["stack_trace"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def setup_handler(log_file, level):
    formatter = JsonFormatter()
    handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=30
    )
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler


def create_log_directories():
    base_path = "log"
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    log_paths = [f"{base_path}/info", f"{base_path}/warning", f"{base_path}/error"]
    for path in log_paths:
        os.makedirs(path, exist_ok=True)


async def initialize_logger(db_name: str, mongo_config: Optional[MongoLogConfig] = None):
    """
    Initialize logger with MongoDB support
    
    Args:
        db_name: Name of the MongoDB database to use
        mongo_config: Optional configuration for collection names
    """
    from ..database.mongo import get_database  # Import your existing database function
    
    create_log_directories()
    
    logger = logging.getLogger("AppLogger")
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    if info_handler := setup_handler("log/info/info.log", logging.INFO):
        logger.addHandler(info_handler)

    if warning_handler := setup_handler("log/warning/warning.log", logging.WARNING):
        logger.addHandler(warning_handler)

    if error_handler := setup_handler("log/error/error.log", logging.ERROR):
        logger.addHandler(error_handler)

    # Add MongoDB handler
    try:
        db = await get_database(db_name)
        if mongo_config is None:
            mongo_config = MongoLogConfig()  # Use default collection names
            
        mongo_handler = MongoDBHandler(db, mongo_config.collections)
        mongo_handler.setLevel(logging.INFO)
        logger.addHandler(mongo_handler)
        await mongo_handler.start()
        
        # Store the MongoDB handler reference for cleanup
        logger.mongo_handler = mongo_handler
    except Exception as e:
        print(f"Failed to initialize MongoDB logging: {e}")
        # Continue with file logging only

    return logger


def get_logger():
    return logging.getLogger("AppLogger")


async def cleanup_logger():
    """Cleanup function to properly shut down the MongoDB handler"""
    logger = get_logger()
    if hasattr(logger, 'mongo_handler'):
        await logger.mongo_handler.stop()