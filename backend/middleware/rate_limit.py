from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
import time
from collections import defaultdict
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter (use Redis in production)
class RateLimiter:
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """Check if request is allowed, returns (allowed, retry_after_seconds)"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_id] = [req_time for req_time in self.requests[client_id] if req_time > minute_ago]
        
        if len(self.requests[client_id]) >= self.requests_per_minute:
            oldest_request = min(self.requests[client_id])
            retry_after = int(60 - (now - oldest_request))
            return False, max(1, retry_after)
        
        self.requests[client_id].append(now)
        return True, 0

# Create rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Get client identifier (IP address or API key)
    client_ip = request.client.host if request.client else "unknown"
    
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/"]:
        return await call_next(request)
    
    allowed, retry_after = rate_limiter.is_allowed(client_ip)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
    
    return await call_next(request)