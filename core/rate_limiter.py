import time
import random
import logging
import requests

logger = logging.getLogger("migration.rate_limiter")

class RateLimitedSession:
    """
    Wrapper around requests.Session that automatically handles
    rate limiting (HTTP 429) and transient server errors (HTTP 5xx)
    with exponential backoff and jitter.
    """
    def __init__(self, max_retries: int = 5, backoff_base: float = 1.5):
        self.session = requests.Session()
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        retries = 0
        while True:
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_time = float(retry_after)
                    else:
                        wait_time = (self.backoff_base ** retries) + random.uniform(0.5, 1.5)
                    
                    if retries >= self.max_retries:
                        logger.error(f"Rate limit exceeded after {retries} retries for {method} {url}")
                        return response
                    
                    logger.warning(f"Rate limited (429) on {url}. Retrying in {wait_time:.2f}s... (Attempt {retries+1}/{self.max_retries})")
                    time.sleep(wait_time)
                    retries += 1
                    continue

                # Check for transient 5xx server errors
                if response.status_code in (500, 502, 503, 504):
                    if retries >= self.max_retries:
                        logger.error(f"Server error ({response.status_code}) after {retries} retries for {method} {url}")
                        return response
                    
                    wait_time = (self.backoff_base ** retries) + random.uniform(0.5, 1.5)
                    logger.warning(f"Server error ({response.status_code}) on {url}. Retrying in {wait_time:.2f}s... (Attempt {retries+1}/{self.max_retries})")
                    time.sleep(wait_time)
                    retries += 1
                    continue

                return response

            except (requests.ConnectionError, requests.Timeout) as e:
                if retries >= self.max_retries:
                    logger.error(f"Network error on {method} {url}: {e}")
                    raise
                
                wait_time = (self.backoff_base ** retries) + random.uniform(1.0, 2.0)
                logger.warning(f"Network error on {url} ({e}). Retrying in {wait_time:.2f}s... (Attempt {retries+1}/{self.max_retries})")
                time.sleep(wait_time)
                retries += 1

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        return self.request("DELETE", url, **kwargs)
