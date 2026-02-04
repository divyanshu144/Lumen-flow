import os
from redis import Redis
from rq import Queue

def get_queue() -> Queue:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    conn = Redis.from_url(redis_url)
    return Queue("default", connection=conn)
