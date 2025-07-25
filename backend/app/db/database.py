"""
Database configuration and session management
"""

from typing import Generator
import logging

logger = logging.getLogger(__name__)


class MockDatabase:
    """Mock database for development"""

    def __init__(self):
        self.connected = True

    def execute(self, query: str):
        """Mock execute"""
        logger.info(f"Mock DB execute: {query}")
        return {"result": "mock"}

    def close(self):
        """Mock close"""
        self.connected = False


# Mock database session
def get_db() -> Generator[MockDatabase, None, None]:
    """Get database session"""
    db = MockDatabase()
    try:
        yield db
    finally:
        db.close()
