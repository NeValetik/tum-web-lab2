"""
Raw socket HTTP/HTTPS client.
No HTTP libraries - uses only socket and ssl modules.
"""

import socket
import ssl
from urllib.parse import urlparse, quote


class HttpResponse:
    """Parsed HTTP response."""

    def __init__(self, status_code, headers, body, url=""):
        self.status_code = status_code
        self.headers = headers
        self.body = body
        self.url = url

    @property
    def content_type(self):
        return self.headers.get("content-type", "")

    @property
    def is_json(self):
        return "application/json" in self.content_type

    @property
    def is_html(self):
        return "text/html" in self.content_type


def parse_url(url):
    """Parse a URL into components. Add scheme if missing."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    parsed = urlparse(url)
    scheme = parsed.scheme
    host = parsed.hostname
    port = parsed.port
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    if port is None:
        port = 443 if scheme == "https" else 80

    return scheme, host, port, path


def build_request(method, host, path, extra_headers=None, accept="text/html, application/json;q=0.9, */*;q=0.8"):
    """Build a raw HTTP/1.1 request string."""
    headers = {
        "Host": host,
        "User-Agent": "go2web/1.0",
        "Accept": accept,
        "Accept-Encoding": "identity",
        "Connection": "close",
    }
    if extra_headers:
        headers.update(extra_headers)

    request = f"{method} {path} HTTP/1.1\r\n"
    for key, value in headers.items():
        request += f"{key}: {value}\r\n"
    request += "\r\n"
    return request


def recv_all(sock):
    """Receive all data from a socket."""
    chunks = []
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
        except socket.timeout:
            break
    return b"".join(chunks)


def parse_response(raw_bytes):
    """Parse raw HTTP response bytes into an HttpResponse."""
    # Split headers from body
    header_end = raw_bytes.find(b"\r\n\r\n")
    if header_end == -1:
        header_end = raw_bytes.find(b"\n\n")
        if header_end == -1:
            return HttpResponse(0, {}, raw_bytes.decode("utf-8", errors="replace"))
        header_bytes = raw_bytes[:header_end]
        body_bytes = raw_bytes[header_end + 2:]
    else:
        header_bytes = raw_bytes[:header_end]
        body_bytes = raw_bytes[header_end + 4:]

    header_text = header_bytes.decode("utf-8", errors="replace")
    lines = header_text.split("\r\n") if "\r\n" in header_text else header_text.split("\n")

    # Parse status line
    status_line = lines[0]
    parts = status_line.split(" ", 2)
    status_code = int(parts[1]) if len(parts) >= 2 else 0

    # Parse headers
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    # Handle chunked transfer encoding
    if headers.get("transfer-encoding", "").lower() == "chunked":
        body_bytes = decode_chunked(body_bytes)

    # Detect encoding from content-type
    encoding = "utf-8"
    ct = headers.get("content-type", "")
    if "charset=" in ct:
        encoding = ct.split("charset=")[-1].split(";")[0].strip()

    body = body_bytes.decode(encoding, errors="replace")

    return HttpResponse(status_code, headers, body)


def decode_chunked(data):
    """Decode chunked transfer encoding."""
    decoded = b""
    idx = 0
    while idx < len(data):
        # Find the end of the chunk size line
        line_end = data.find(b"\r\n", idx)
        if line_end == -1:
            break

        # Parse chunk size (hex)
        size_str = data[idx:line_end].decode("ascii", errors="replace").strip()
        if not size_str:
            idx = line_end + 2
            continue

        try:
            chunk_size = int(size_str.split(";")[0], 16)
        except ValueError:
            break

        if chunk_size == 0:
            break

        # Extract chunk data
        chunk_start = line_end + 2
        chunk_end = chunk_start + chunk_size
        if chunk_end > len(data):
            decoded += data[chunk_start:]
            break
        decoded += data[chunk_start:chunk_end]

        # Move past chunk data and trailing \r\n
        idx = chunk_end + 2

    return decoded


def http_request(url, max_redirects=5, accept="text/html, application/json;q=0.9, */*;q=0.8", use_cache=True):
    """
    Make an HTTP/HTTPS request using raw sockets.
    Follows redirects up to max_redirects times.
    Supports HTTP caching with Cache-Control, ETag, and Last-Modified.
    """
    from cache import get_cached, save_to_cache, get_validation_headers

    # Check cache first
    if use_cache:
        cached, is_fresh = get_cached(url)
        if cached and is_fresh:
            print("  [cache] Using cached response")
            return HttpResponse(
                cached["status_code"], cached["headers"],
                cached["body"], cached["url"]
            )

    for _ in range(max_redirects + 1):
        scheme, host, port, path = parse_url(url)

        extra_headers = {}
        if use_cache:
            extra_headers = get_validation_headers(url)

        request_str = build_request("GET", host, path, extra_headers=extra_headers, accept=accept)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)

        try:
            # Wrap with SSL if HTTPS
            if scheme == "https":
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=host)

            sock.connect((host, port))
            sock.sendall(request_str.encode("utf-8"))

            raw = recv_all(sock)
        finally:
            sock.close()

        response = parse_response(raw)
        response.url = url

        # Handle 304 Not Modified - use cached version
        if response.status_code == 304 and use_cache:
            cached, _ = get_cached(url)
            if cached:
                print("  [cache] Not modified, using cached response")
                return HttpResponse(
                    cached["status_code"], cached["headers"],
                    cached["body"], cached["url"]
                )

        # Handle redirects (3xx)
        if 300 <= response.status_code < 400:
            location = response.headers.get("location", "")
            if not location:
                return response

            # Handle relative redirects
            if location.startswith("/"):
                location = f"{scheme}://{host}{location}"
            elif not location.startswith("http"):
                location = f"{scheme}://{host}/{location}"

            print(f"  -> Redirecting to {location}")
            url = location
            continue

        # Cache successful responses
        if use_cache and 200 <= response.status_code < 300:
            save_to_cache(url, response)

        return response

    print("  [!] Too many redirects")
    return response
