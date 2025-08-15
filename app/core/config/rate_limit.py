from fastapi_limiter.depends import RateLimiter

RATE_LIMITS = {
    "data": RateLimiter(times=60, seconds=60),
    "fetch": RateLimiter(times=10, seconds=60),
    "task_status": RateLimiter(times=30, seconds=60),
    "task_management": RateLimiter(times=20, seconds=60),
    "health": RateLimiter(times=100, seconds=60),
    "root": RateLimiter(times=200, seconds=60),
}

DEFAULT_RATE_LIMIT = RateLimiter(times=30, seconds=60)


def get_rate_limit(endpoint_type: str) -> RateLimiter:
    return RATE_LIMITS.get(endpoint_type, DEFAULT_RATE_LIMIT)
