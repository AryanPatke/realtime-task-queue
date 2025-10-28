import redis.asyncio as redis
from app.core.config import settings
from typing import Optional


class RedisClient:
    """Redis client for task queue management"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        self.client = await redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
        return self.client
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
    
    def get_client(self) -> redis.Redis:
        """Get Redis client instance"""
        if not self.client:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self.client


redis_client = RedisClient()

