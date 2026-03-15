"""
HTTP cache mechanism using file-based storage.
Respects Cache-Control headers and ETag/Last-Modified for validation.
"""

import os
import json
import time
import hashlib


CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".go2web_cache")


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_key(url):
    """Generate a cache key from a URL."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _cache_path(url):
    """Get the file path for a cached URL."""
    return os.path.join(CACHE_DIR, _cache_key(url) + ".json")


def get_cached(url):
    """
    Get a cached response for a URL.
    Returns (cached_response_dict, is_fresh) or (None, False).
    cached_response_dict has keys: status_code, headers, body, url, cached_at
    """
    path = _cache_path(url)
    if not os.path.exists(path):
        return None, False

    try:
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None, False

    # Check if cache is fresh based on max-age
    cached_at = entry.get("cached_at", 0)
    max_age = entry.get("max_age", 300)  # default 5 min
    age = time.time() - cached_at

    is_fresh = age < max_age
    return entry, is_fresh


def save_to_cache(url, response):
    """Save an HTTP response to the cache."""
    _ensure_cache_dir()

    # Parse Cache-Control for max-age
    cache_control = response.headers.get("cache-control", "")
    max_age = 300  # default 5 minutes

    if "no-store" in cache_control or "no-cache" in cache_control:
        return  # Don't cache

    if "max-age=" in cache_control:
        try:
            max_age = int(cache_control.split("max-age=")[1].split(",")[0].strip())
        except (ValueError, IndexError):
            pass

    entry = {
        "status_code": response.status_code,
        "headers": response.headers,
        "body": response.body,
        "url": response.url,
        "cached_at": time.time(),
        "max_age": max_age,
        "etag": response.headers.get("etag", ""),
        "last_modified": response.headers.get("last-modified", ""),
    }

    path = _cache_path(url)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f)
    except IOError:
        pass  # Silently fail on cache write errors


def get_validation_headers(url):
    """Get conditional request headers if we have a stale cache entry."""
    entry, _ = get_cached(url)
    if entry is None:
        return {}

    headers = {}
    if entry.get("etag"):
        headers["If-None-Match"] = entry["etag"]
    if entry.get("last_modified"):
        headers["If-Modified-Since"] = entry["last_modified"]

    return headers


def clear_cache():
    """Clear the entire cache."""
    if os.path.exists(CACHE_DIR):
        for f in os.listdir(CACHE_DIR):
            path = os.path.join(CACHE_DIR, f)
            if os.path.isfile(path):
                os.remove(path)
        print("Cache cleared.")
    else:
        print("No cache to clear.")
