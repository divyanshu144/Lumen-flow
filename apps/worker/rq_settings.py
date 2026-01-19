import os
from redis import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
conn = Redis.from_url(REDIS_URL)
