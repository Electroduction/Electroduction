#!/usr/bin/env python3
"""
API Toolkit
===========

A comprehensive toolkit for building and consuming APIs.
Provides client utilities, request builders, and response handling.

Author: Electroduction Security Team
Version: 1.0.0

Features:
---------
- HTTP Client: Full-featured HTTP client with retry logic
- Request Builder: Fluent interface for building requests
- Response Handling: Parse and validate responses
- Authentication: Support for various auth methods
- Rate Limiting: Built-in rate limiting
- Caching: Response caching support
- API Mocking: Mock API responses for testing

Usage:
------
    from api_toolkit import APIClient, RequestBuilder, RESTClient

    # Create a REST API client
    client = RESTClient("https://api.example.com")

    # Make authenticated requests
    client.auth_bearer("token123")
    users = client.get("/users").json()

    # Build complex requests
    response = (RequestBuilder("https://api.example.com")
                .post("/users")
                .json({"name": "John"})
                .header("X-Custom", "value")
                .send())
"""

import os
import re
import json
import time
import hashlib
import base64
import urllib.request
import urllib.parse
import urllib.error
import ssl
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from functools import wraps


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class APIResponse:
    """
    Represents an API response.

    Provides convenient access to response data, headers, and status.
    """
    url: str
    method: str
    status_code: int
    headers: Dict[str, str]
    content: bytes
    elapsed_ms: float
    request_headers: Dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """Check if response indicates success (2xx status)."""
        return 200 <= self.status_code < 300

    @property
    def text(self) -> str:
        """Get response as text."""
        encoding = self._detect_encoding()
        try:
            return self.content.decode(encoding)
        except UnicodeDecodeError:
            return self.content.decode('utf-8', errors='replace')

    @property
    def json_data(self) -> Any:
        """Parse response as JSON."""
        return json.loads(self.text)

    def json(self) -> Any:
        """Parse response as JSON (alias for json_data)."""
        return self.json_data

    def _detect_encoding(self) -> str:
        """Detect response encoding from headers."""
        content_type = self.headers.get('content-type', '')
        match = re.search(r'charset=([^\s;]+)', content_type)
        return match.group(1) if match else 'utf-8'

    def raise_for_status(self):
        """Raise exception if response indicates error."""
        if not self.ok:
            raise APIError(
                f"HTTP {self.status_code}",
                response=self
            )


@dataclass
class APIError(Exception):
    """Exception raised for API errors."""
    message: str
    response: Optional[APIResponse] = None
    cause: Optional[Exception] = None

    def __str__(self):
        if self.response:
            return f"{self.message}: {self.response.text[:200]}"
        return self.message


# =============================================================================
# AUTHENTICATION
# =============================================================================

class AuthMethod:
    """Base class for authentication methods."""

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Apply authentication to headers."""
        return headers


class NoAuth(AuthMethod):
    """No authentication."""
    pass


class BearerAuth(AuthMethod):
    """Bearer token authentication."""

    def __init__(self, token: str):
        self.token = token

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        headers['Authorization'] = f'Bearer {self.token}'
        return headers


class BasicAuth(AuthMethod):
    """HTTP Basic authentication."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers['Authorization'] = f'Basic {encoded}'
        return headers


class APIKeyAuth(AuthMethod):
    """API key authentication."""

    def __init__(self, key: str, header_name: str = 'X-API-Key'):
        self.key = key
        self.header_name = header_name

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        headers[self.header_name] = self.key
        return headers


class CustomAuth(AuthMethod):
    """Custom authentication using a callback."""

    def __init__(self, callback: Callable[[Dict[str, str]], Dict[str, str]]):
        self.callback = callback

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        return self.callback(headers)


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Features:
    - Configurable requests per second
    - Burst allowance
    - Per-endpoint limiting
    """

    def __init__(self, requests_per_second: float = 10.0, burst: int = 20):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum sustained request rate
            burst: Maximum burst size
        """
        self.rate = requests_per_second
        self.burst = burst
        self._tokens: Dict[str, float] = {}
        self._last_update: Dict[str, float] = {}
        self._lock = threading.Lock()

    def acquire(self, key: str = '_global'):
        """
        Acquire permission to make a request.

        Blocks until a request is allowed.
        """
        now = time.time()

        with self._lock:
            if key not in self._tokens:
                self._tokens[key] = self.burst
                self._last_update[key] = now

            # Add tokens based on elapsed time
            elapsed = now - self._last_update[key]
            self._tokens[key] = min(
                self.burst,
                self._tokens[key] + elapsed * self.rate
            )
            self._last_update[key] = now

            # Wait if no tokens available
            if self._tokens[key] < 1:
                wait_time = (1 - self._tokens[key]) / self.rate
                time.sleep(wait_time)
                self._tokens[key] = 0
            else:
                self._tokens[key] -= 1


# =============================================================================
# RESPONSE CACHE
# =============================================================================

@dataclass
class CacheEntry:
    """Cache entry with expiration."""
    response: APIResponse
    expires_at: datetime
    etag: Optional[str] = None
    last_modified: Optional[str] = None


class ResponseCache:
    """
    Simple in-memory response cache.

    Features:
    - TTL-based expiration
    - ETag/Last-Modified support
    - Size limits
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of cached responses
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()

    def _make_key(self, method: str, url: str, headers: Dict[str, str]) -> str:
        """Generate cache key."""
        # Include relevant headers in cache key
        relevant_headers = {
            k: v for k, v in sorted(headers.items())
            if k.lower() in ('accept', 'authorization')
        }
        key_data = f"{method}:{url}:{json.dumps(relevant_headers, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, method: str, url: str, headers: Dict[str, str]) -> Optional[CacheEntry]:
        """Get cached response if valid."""
        if method.upper() != 'GET':
            return None

        key = self._make_key(method, url, headers)

        with self._lock:
            entry = self._cache.get(key)

            if entry:
                if datetime.now() < entry.expires_at:
                    # Move to end (LRU)
                    self._cache.move_to_end(key)
                    return entry
                else:
                    # Expired
                    del self._cache[key]

        return None

    def put(self, method: str, url: str, headers: Dict[str, str],
            response: APIResponse, ttl: Optional[int] = None):
        """Cache a response."""
        if method.upper() != 'GET':
            return

        key = self._make_key(method, url, headers)
        ttl = ttl or self.default_ttl

        entry = CacheEntry(
            response=response,
            expires_at=datetime.now() + timedelta(seconds=ttl),
            etag=response.headers.get('etag'),
            last_modified=response.headers.get('last-modified')
        )

        with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = entry

    def invalidate(self, url_pattern: Optional[str] = None):
        """Invalidate cache entries."""
        with self._lock:
            if url_pattern:
                # Remove matching entries
                to_remove = [
                    k for k, v in self._cache.items()
                    if url_pattern in v.response.url
                ]
                for k in to_remove:
                    del self._cache[k]
            else:
                # Clear all
                self._cache.clear()


# =============================================================================
# REQUEST BUILDER
# =============================================================================

class RequestBuilder:
    """
    Fluent interface for building HTTP requests.

    Example:
        >>> response = (RequestBuilder("https://api.example.com")
        ...     .post("/users")
        ...     .json({"name": "John"})
        ...     .header("X-Request-ID", "123")
        ...     .timeout(30)
        ...     .send())
    """

    def __init__(self, base_url: str = ""):
        """Initialize request builder."""
        self._base_url = base_url.rstrip('/')
        self._method = 'GET'
        self._path = ''
        self._headers: Dict[str, str] = {}
        self._query_params: Dict[str, str] = {}
        self._body: Optional[bytes] = None
        self._timeout = 30.0
        self._auth: AuthMethod = NoAuth()
        self._verify_ssl = True

    def get(self, path: str = '') -> 'RequestBuilder':
        """Set GET method and path."""
        self._method = 'GET'
        self._path = path
        return self

    def post(self, path: str = '') -> 'RequestBuilder':
        """Set POST method and path."""
        self._method = 'POST'
        self._path = path
        return self

    def put(self, path: str = '') -> 'RequestBuilder':
        """Set PUT method and path."""
        self._method = 'PUT'
        self._path = path
        return self

    def patch(self, path: str = '') -> 'RequestBuilder':
        """Set PATCH method and path."""
        self._method = 'PATCH'
        self._path = path
        return self

    def delete(self, path: str = '') -> 'RequestBuilder':
        """Set DELETE method and path."""
        self._method = 'DELETE'
        self._path = path
        return self

    def head(self, path: str = '') -> 'RequestBuilder':
        """Set HEAD method and path."""
        self._method = 'HEAD'
        self._path = path
        return self

    def options(self, path: str = '') -> 'RequestBuilder':
        """Set OPTIONS method and path."""
        self._method = 'OPTIONS'
        self._path = path
        return self

    def header(self, name: str, value: str) -> 'RequestBuilder':
        """Add a header."""
        self._headers[name] = value
        return self

    def headers(self, headers: Dict[str, str]) -> 'RequestBuilder':
        """Add multiple headers."""
        self._headers.update(headers)
        return self

    def param(self, name: str, value: Any) -> 'RequestBuilder':
        """Add a query parameter."""
        self._query_params[name] = str(value)
        return self

    def params(self, params: Dict[str, Any]) -> 'RequestBuilder':
        """Add multiple query parameters."""
        for k, v in params.items():
            self._query_params[k] = str(v)
        return self

    def json(self, data: Any) -> 'RequestBuilder':
        """Set JSON body."""
        self._body = json.dumps(data).encode('utf-8')
        self._headers['Content-Type'] = 'application/json'
        return self

    def form(self, data: Dict[str, Any]) -> 'RequestBuilder':
        """Set form data body."""
        self._body = urllib.parse.urlencode(data).encode('utf-8')
        self._headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return self

    def body(self, data: Union[str, bytes], content_type: str = 'text/plain') -> 'RequestBuilder':
        """Set raw body."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        self._body = data
        self._headers['Content-Type'] = content_type
        return self

    def timeout(self, seconds: float) -> 'RequestBuilder':
        """Set request timeout."""
        self._timeout = seconds
        return self

    def auth(self, auth_method: AuthMethod) -> 'RequestBuilder':
        """Set authentication method."""
        self._auth = auth_method
        return self

    def bearer(self, token: str) -> 'RequestBuilder':
        """Set bearer token authentication."""
        self._auth = BearerAuth(token)
        return self

    def basic(self, username: str, password: str) -> 'RequestBuilder':
        """Set basic authentication."""
        self._auth = BasicAuth(username, password)
        return self

    def api_key(self, key: str, header: str = 'X-API-Key') -> 'RequestBuilder':
        """Set API key authentication."""
        self._auth = APIKeyAuth(key, header)
        return self

    def verify(self, verify: bool = True) -> 'RequestBuilder':
        """Set SSL verification."""
        self._verify_ssl = verify
        return self

    def build_url(self) -> str:
        """Build the full URL."""
        url = self._base_url + self._path

        if self._query_params:
            query = urllib.parse.urlencode(self._query_params)
            url = f"{url}?{query}"

        return url

    def build_headers(self) -> Dict[str, str]:
        """Build final headers with auth."""
        headers = dict(self._headers)
        headers = self._auth.apply(headers)

        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'APIToolkit/1.0'

        return headers

    def send(self) -> APIResponse:
        """Send the request and return response."""
        url = self.build_url()
        headers = self.build_headers()

        start_time = time.time()

        # Create SSL context
        if self._verify_ssl:
            ssl_context = ssl.create_default_context()
        else:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        try:
            request = urllib.request.Request(
                url,
                data=self._body,
                headers=headers,
                method=self._method
            )

            with urllib.request.urlopen(
                request,
                timeout=self._timeout,
                context=ssl_context
            ) as response:
                content = response.read()
                elapsed = (time.time() - start_time) * 1000

                return APIResponse(
                    url=response.geturl(),
                    method=self._method,
                    status_code=response.status,
                    headers=dict(response.headers),
                    content=content,
                    elapsed_ms=elapsed,
                    request_headers=headers
                )

        except urllib.error.HTTPError as e:
            elapsed = (time.time() - start_time) * 1000
            content = e.read() if hasattr(e, 'read') else b''

            return APIResponse(
                url=url,
                method=self._method,
                status_code=e.code,
                headers=dict(e.headers) if hasattr(e, 'headers') else {},
                content=content,
                elapsed_ms=elapsed,
                request_headers=headers
            )

        except urllib.error.URLError as e:
            elapsed = (time.time() - start_time) * 1000
            raise APIError(f"Connection error: {e.reason}")


# =============================================================================
# API CLIENT
# =============================================================================

class APIClient:
    """
    Full-featured HTTP API client.

    Features:
    - Request building
    - Authentication
    - Rate limiting
    - Response caching
    - Retry logic

    Example:
        >>> client = APIClient("https://api.example.com")
        >>> client.auth_bearer("token123")
        >>> response = client.get("/users")
    """

    def __init__(self, base_url: str = "", timeout: float = 30.0):
        """
        Initialize API client.

        Args:
            base_url: Base URL for all requests
            timeout: Default timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.default_headers: Dict[str, str] = {
            'Accept': 'application/json',
            'User-Agent': 'APIToolkit/1.0'
        }
        self._auth: AuthMethod = NoAuth()
        self._rate_limiter: Optional[RateLimiter] = None
        self._cache: Optional[ResponseCache] = None
        self._verify_ssl = True

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        self.retry_statuses = {429, 500, 502, 503, 504}

    def set_header(self, name: str, value: str) -> 'APIClient':
        """Set a default header."""
        self.default_headers[name] = value
        return self

    def auth(self, auth_method: AuthMethod) -> 'APIClient':
        """Set authentication method."""
        self._auth = auth_method
        return self

    def auth_bearer(self, token: str) -> 'APIClient':
        """Set bearer token authentication."""
        self._auth = BearerAuth(token)
        return self

    def auth_basic(self, username: str, password: str) -> 'APIClient':
        """Set basic authentication."""
        self._auth = BasicAuth(username, password)
        return self

    def auth_api_key(self, key: str, header: str = 'X-API-Key') -> 'APIClient':
        """Set API key authentication."""
        self._auth = APIKeyAuth(key, header)
        return self

    def enable_rate_limiting(self, requests_per_second: float = 10.0, burst: int = 20):
        """Enable rate limiting."""
        self._rate_limiter = RateLimiter(requests_per_second, burst)

    def enable_caching(self, max_size: int = 1000, default_ttl: int = 300):
        """Enable response caching."""
        self._cache = ResponseCache(max_size, default_ttl)

    def disable_ssl_verify(self):
        """Disable SSL certificate verification."""
        self._verify_ssl = False

    def _build_request(self, method: str, path: str,
                       params: Optional[Dict[str, Any]] = None,
                       json_data: Optional[Any] = None,
                       data: Optional[Dict[str, Any]] = None,
                       headers: Optional[Dict[str, str]] = None) -> RequestBuilder:
        """Build a request."""
        builder = RequestBuilder(self.base_url)

        # Set method
        method_func = getattr(builder, method.lower())
        method_func(path)

        # Add headers
        for k, v in self.default_headers.items():
            builder.header(k, v)
        if headers:
            builder.headers(headers)

        # Add params
        if params:
            builder.params(params)

        # Add body
        if json_data is not None:
            builder.json(json_data)
        elif data is not None:
            builder.form(data)

        # Set auth and options
        builder.auth(self._auth)
        builder.timeout(self.timeout)
        builder.verify(self._verify_ssl)

        return builder

    def _send_with_retry(self, builder: RequestBuilder) -> APIResponse:
        """Send request with retry logic."""
        last_error = None

        for attempt in range(self.max_retries + 1):
            # Rate limiting
            if self._rate_limiter:
                self._rate_limiter.acquire()

            try:
                response = builder.send()

                # Check if should retry
                if response.status_code in self.retry_statuses and attempt < self.max_retries:
                    # Respect Retry-After header
                    retry_after = response.headers.get('retry-after')
                    if retry_after:
                        try:
                            delay = int(retry_after)
                        except ValueError:
                            delay = self.retry_delay * (2 ** attempt)
                    else:
                        delay = self.retry_delay * (2 ** attempt)

                    time.sleep(delay)
                    continue

                return response

            except APIError as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise

        raise last_error or APIError("Max retries exceeded")

    def request(self, method: str, path: str,
                params: Optional[Dict[str, Any]] = None,
                json: Optional[Any] = None,
                data: Optional[Dict[str, Any]] = None,
                headers: Optional[Dict[str, str]] = None) -> APIResponse:
        """
        Make an HTTP request.

        Args:
            method: HTTP method
            path: URL path
            params: Query parameters
            json: JSON body
            data: Form data
            headers: Additional headers

        Returns:
            APIResponse object
        """
        builder = self._build_request(method, path, params, json, data, headers)

        # Check cache for GET requests
        if method.upper() == 'GET' and self._cache:
            url = builder.build_url()
            cached = self._cache.get(method, url, builder.build_headers())
            if cached:
                return cached.response

        response = self._send_with_retry(builder)

        # Cache successful GET responses
        if method.upper() == 'GET' and self._cache and response.ok:
            url = builder.build_url()
            self._cache.put(method, url, builder.build_headers(), response)

        return response

    def get(self, path: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> APIResponse:
        """Make GET request."""
        return self.request('GET', path, params=params, headers=headers)

    def post(self, path: str, json: Optional[Any] = None,
             data: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None) -> APIResponse:
        """Make POST request."""
        return self.request('POST', path, json=json, data=data, headers=headers)

    def put(self, path: str, json: Optional[Any] = None,
            data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> APIResponse:
        """Make PUT request."""
        return self.request('PUT', path, json=json, data=data, headers=headers)

    def patch(self, path: str, json: Optional[Any] = None,
              data: Optional[Dict[str, Any]] = None,
              headers: Optional[Dict[str, str]] = None) -> APIResponse:
        """Make PATCH request."""
        return self.request('PATCH', path, json=json, data=data, headers=headers)

    def delete(self, path: str, params: Optional[Dict[str, Any]] = None,
               headers: Optional[Dict[str, str]] = None) -> APIResponse:
        """Make DELETE request."""
        return self.request('DELETE', path, params=params, headers=headers)


# =============================================================================
# REST CLIENT (CONVENIENCE WRAPPER)
# =============================================================================

class RESTClient(APIClient):
    """
    REST API client with resource-based interface.

    Example:
        >>> client = RESTClient("https://api.example.com")
        >>> users = client.resource("users")
        >>>
        >>> # CRUD operations
        >>> all_users = users.list()
        >>> user = users.get(1)
        >>> new_user = users.create({"name": "John"})
        >>> updated = users.update(1, {"name": "Jane"})
        >>> users.delete(1)
    """

    def resource(self, name: str) -> 'Resource':
        """Get a resource helper."""
        return Resource(self, name)


class Resource:
    """
    RESTful resource helper.

    Provides CRUD operations for a REST resource.
    """

    def __init__(self, client: RESTClient, name: str):
        """Initialize resource."""
        self.client = client
        self.name = name
        self.path = f"/{name}"

    def list(self, params: Optional[Dict[str, Any]] = None) -> List[Any]:
        """List all resources (GET /resources)."""
        response = self.client.get(self.path, params=params)
        response.raise_for_status()
        return response.json()

    def get(self, id: Union[int, str]) -> Any:
        """Get single resource (GET /resources/:id)."""
        response = self.client.get(f"{self.path}/{id}")
        response.raise_for_status()
        return response.json()

    def create(self, data: Dict[str, Any]) -> Any:
        """Create resource (POST /resources)."""
        response = self.client.post(self.path, json=data)
        response.raise_for_status()
        return response.json()

    def update(self, id: Union[int, str], data: Dict[str, Any]) -> Any:
        """Update resource (PUT /resources/:id)."""
        response = self.client.put(f"{self.path}/{id}", json=data)
        response.raise_for_status()
        return response.json()

    def partial_update(self, id: Union[int, str], data: Dict[str, Any]) -> Any:
        """Partial update (PATCH /resources/:id)."""
        response = self.client.patch(f"{self.path}/{id}", json=data)
        response.raise_for_status()
        return response.json()

    def delete(self, id: Union[int, str]) -> bool:
        """Delete resource (DELETE /resources/:id)."""
        response = self.client.delete(f"{self.path}/{id}")
        response.raise_for_status()
        return True


# =============================================================================
# API MOCK SERVER
# =============================================================================

class MockResponse:
    """Mock response configuration."""

    def __init__(self, status: int = 200, json_data: Any = None,
                 text: str = "", headers: Optional[Dict[str, str]] = None,
                 delay: float = 0):
        """Configure mock response."""
        self.status = status
        self.json_data = json_data
        self.text = text
        self.headers = headers or {}
        self.delay = delay


class APIMock:
    """
    Mock API responses for testing.

    Example:
        >>> mock = APIMock()
        >>> mock.register("GET", "/users", MockResponse(
        ...     status=200,
        ...     json_data=[{"id": 1, "name": "John"}]
        ... ))
        >>>
        >>> response = mock.handle("GET", "/users")
        >>> print(response.json())
    """

    def __init__(self):
        """Initialize mock."""
        self._routes: Dict[str, Dict[str, MockResponse]] = {}
        self._call_history: List[Dict[str, Any]] = []

    def register(self, method: str, path: str, response: MockResponse):
        """Register a mock response."""
        method = method.upper()
        if method not in self._routes:
            self._routes[method] = {}
        self._routes[method][path] = response

    def register_json(self, method: str, path: str, data: Any, status: int = 200):
        """Convenience method to register JSON response."""
        self.register(method, path, MockResponse(status=status, json_data=data))

    def handle(self, method: str, path: str,
               body: Optional[Any] = None) -> APIResponse:
        """Handle a mock request."""
        method = method.upper()

        # Record call
        self._call_history.append({
            'method': method,
            'path': path,
            'body': body,
            'timestamp': datetime.now()
        })

        # Find matching route
        routes = self._routes.get(method, {})

        # Exact match
        if path in routes:
            mock = routes[path]
        else:
            # Pattern match
            mock = None
            for pattern, response in routes.items():
                if self._path_matches(pattern, path):
                    mock = response
                    break

        if not mock:
            return APIResponse(
                url=path,
                method=method,
                status_code=404,
                headers={'content-type': 'application/json'},
                content=b'{"error": "Not Found"}',
                elapsed_ms=0
            )

        # Apply delay
        if mock.delay > 0:
            time.sleep(mock.delay)

        # Build response
        if mock.json_data is not None:
            content = json.dumps(mock.json_data).encode('utf-8')
            headers = {'content-type': 'application/json', **mock.headers}
        else:
            content = mock.text.encode('utf-8')
            headers = {'content-type': 'text/plain', **mock.headers}

        return APIResponse(
            url=path,
            method=method,
            status_code=mock.status,
            headers=headers,
            content=content,
            elapsed_ms=mock.delay * 1000
        )

    def _path_matches(self, pattern: str, path: str) -> bool:
        """Check if path matches pattern with wildcards."""
        # Convert pattern to regex
        regex_pattern = pattern.replace('*', '[^/]+').replace('**', '.*')
        regex_pattern = f'^{regex_pattern}$'
        return bool(re.match(regex_pattern, path))

    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get history of mock calls."""
        return self._call_history.copy()

    def assert_called(self, method: str, path: str, times: int = 1) -> bool:
        """Assert a route was called expected number of times."""
        count = sum(
            1 for call in self._call_history
            if call['method'] == method.upper() and call['path'] == path
        )
        return count == times

    def reset(self):
        """Reset call history."""
        self._call_history.clear()


# =============================================================================
# RESPONSE VALIDATOR
# =============================================================================

class ResponseValidator:
    """
    Validate API responses against expected schema.

    Example:
        >>> validator = ResponseValidator()
        >>> validator.expect_status(200)
        >>> validator.expect_json_key("id")
        >>> validator.expect_json_key("name", str)
        >>> is_valid = validator.validate(response)
    """

    def __init__(self):
        """Initialize validator."""
        self._status: Optional[int] = None
        self._status_range: Optional[Tuple[int, int]] = None
        self._content_type: Optional[str] = None
        self._json_keys: Dict[str, Optional[type]] = {}
        self._json_schema: Optional[Dict] = None
        self._headers: Dict[str, Optional[str]] = {}

    def expect_status(self, status: int) -> 'ResponseValidator':
        """Expect specific status code."""
        self._status = status
        return self

    def expect_status_range(self, start: int, end: int) -> 'ResponseValidator':
        """Expect status code in range."""
        self._status_range = (start, end)
        return self

    def expect_success(self) -> 'ResponseValidator':
        """Expect 2xx status."""
        return self.expect_status_range(200, 299)

    def expect_content_type(self, content_type: str) -> 'ResponseValidator':
        """Expect specific content type."""
        self._content_type = content_type
        return self

    def expect_json(self) -> 'ResponseValidator':
        """Expect JSON response."""
        return self.expect_content_type('application/json')

    def expect_json_key(self, key: str, value_type: Optional[type] = None) -> 'ResponseValidator':
        """Expect JSON to contain key."""
        self._json_keys[key] = value_type
        return self

    def expect_header(self, name: str, value: Optional[str] = None) -> 'ResponseValidator':
        """Expect header to exist (and optionally have value)."""
        self._headers[name.lower()] = value
        return self

    def validate(self, response: APIResponse) -> Tuple[bool, List[str]]:
        """
        Validate response.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check status
        if self._status is not None and response.status_code != self._status:
            errors.append(f"Expected status {self._status}, got {response.status_code}")

        if self._status_range:
            start, end = self._status_range
            if not (start <= response.status_code <= end):
                errors.append(f"Expected status in {start}-{end}, got {response.status_code}")

        # Check content type
        if self._content_type:
            content_type = response.headers.get('content-type', '')
            if self._content_type not in content_type:
                errors.append(f"Expected content-type {self._content_type}, got {content_type}")

        # Check headers
        for name, expected_value in self._headers.items():
            actual_value = response.headers.get(name)
            if actual_value is None:
                errors.append(f"Missing header: {name}")
            elif expected_value is not None and actual_value != expected_value:
                errors.append(f"Header {name}: expected {expected_value}, got {actual_value}")

        # Check JSON keys
        if self._json_keys:
            try:
                data = response.json()
                for key, expected_type in self._json_keys.items():
                    if key not in data:
                        errors.append(f"Missing JSON key: {key}")
                    elif expected_type is not None and not isinstance(data[key], expected_type):
                        errors.append(f"Key {key}: expected {expected_type.__name__}, got {type(data[key]).__name__}")
            except json.JSONDecodeError:
                errors.append("Response is not valid JSON")

        return len(errors) == 0, errors


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Command-line interface for the API Toolkit."""
    print("=" * 60)
    print("API TOOLKIT")
    print("=" * 60)
    print()

    # Demo: Request Builder
    print("1. REQUEST BUILDER DEMO")
    print("-" * 40)

    builder = RequestBuilder("https://api.example.com")
    builder.get("/users")
    builder.param("page", 1)
    builder.param("limit", 10)
    builder.header("Accept", "application/json")
    builder.bearer("test-token")

    print(f"URL: {builder.build_url()}")
    print(f"Headers: {builder.build_headers()}")
    print()

    # Demo: API Mock
    print("2. API MOCK DEMO")
    print("-" * 40)

    mock = APIMock()

    # Register mock responses
    mock.register_json("GET", "/users", [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"}
    ])

    mock.register_json("GET", "/users/1", {
        "id": 1, "name": "Alice", "email": "alice@example.com"
    })

    mock.register_json("POST", "/users", {
        "id": 3, "name": "Charlie", "email": "charlie@example.com"
    }, status=201)

    # Make mock requests
    response = mock.handle("GET", "/users")
    print(f"GET /users: {response.status_code}")
    print(f"  Data: {response.json()}")

    response = mock.handle("GET", "/users/1")
    print(f"GET /users/1: {response.status_code}")
    print(f"  Data: {response.json()}")

    response = mock.handle("POST", "/users", {"name": "Charlie"})
    print(f"POST /users: {response.status_code}")
    print(f"  Data: {response.json()}")

    response = mock.handle("GET", "/nonexistent")
    print(f"GET /nonexistent: {response.status_code}")
    print()

    # Demo: Authentication Methods
    print("3. AUTHENTICATION DEMO")
    print("-" * 40)

    # Bearer auth
    bearer = BearerAuth("my-secret-token")
    headers = bearer.apply({})
    print(f"Bearer Auth: {headers.get('Authorization')}")

    # Basic auth
    basic = BasicAuth("user", "pass")
    headers = basic.apply({})
    print(f"Basic Auth: {headers.get('Authorization')}")

    # API key
    api_key = APIKeyAuth("api-key-123", "X-API-Key")
    headers = api_key.apply({})
    print(f"API Key Auth: {headers.get('X-API-Key')}")
    print()

    # Demo: Response Validation
    print("4. RESPONSE VALIDATION DEMO")
    print("-" * 40)

    # Create a mock response to validate
    test_response = APIResponse(
        url="/users",
        method="GET",
        status_code=200,
        headers={"content-type": "application/json"},
        content=json.dumps({"id": 1, "name": "Alice", "age": "thirty"}).encode(),
        elapsed_ms=100
    )

    validator = ResponseValidator()
    validator.expect_success()
    validator.expect_json()
    validator.expect_json_key("id", int)
    validator.expect_json_key("name", str)
    validator.expect_json_key("age", int)  # Will fail - age is string

    is_valid, errors = validator.validate(test_response)
    print(f"Response valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    print()

    # Demo: Rate Limiter
    print("5. RATE LIMITER DEMO")
    print("-" * 40)

    limiter = RateLimiter(requests_per_second=5.0, burst=3)
    print(f"Rate: {limiter.rate} req/s, Burst: {limiter.burst}")

    start = time.time()
    for i in range(5):
        limiter.acquire("test")
        elapsed = time.time() - start
        print(f"  Request {i+1} at {elapsed:.3f}s")
    print()

    # Demo: Response Cache
    print("6. RESPONSE CACHE DEMO")
    print("-" * 40)

    cache = ResponseCache(max_size=100, default_ttl=60)

    # Cache a response
    cached_response = APIResponse(
        url="/data",
        method="GET",
        status_code=200,
        headers={},
        content=b'{"cached": true}',
        elapsed_ms=50
    )

    cache.put("GET", "/data", {}, cached_response)
    print("Response cached")

    # Retrieve from cache
    entry = cache.get("GET", "/data", {})
    if entry:
        print(f"Cache hit: {entry.response.text}")
    else:
        print("Cache miss")
    print()

    # Demo: Call History
    print("7. MOCK CALL HISTORY")
    print("-" * 40)

    history = mock.get_call_history()
    print(f"Total calls: {len(history)}")
    for call in history:
        print(f"  {call['method']} {call['path']}")

    print(f"\nGET /users called: {mock.assert_called('GET', '/users', 1)}")
    print()

    print("=" * 60)
    print("API Toolkit Demo Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
