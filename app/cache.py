import os
import json
import redis

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)

CACHE_TTL = 60 * 60  # 缓存1小时

def get_cache(query: str) -> dict | None:
    try:
        value = redis_client.get(query)
        if value:
            return json.loads(value)
    except Exception as e:
        print(f"Redis cache GET error: {e}")
    return None

def set_cache(query: str, result: dict) -> None:
    try:
        redis_client.setex(query, CACHE_TTL, json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(f"Redis cache SET error: {e}")
