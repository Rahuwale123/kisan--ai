from functools import lru_cache
import hashlib

def generate_cache_key(*args, **kwargs):
    """Generate a unique cache key based on function arguments"""
    key = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key.encode()).hexdigest()

def cache_response(timeout=300):
    """Custom caching decorator for responses"""
    def decorator(func):
        @lru_cache(maxsize=100)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator 