"""
go2web - A command-line HTTP client built on raw TCP sockets.
No HTTP libraries used - all requests are made via socket + ssl.
"""

import sys
import argparse

from http_client import http_request
from html_parser import format_response


def print_help():
    """Print usage help."""
    print("go2web - A command-line HTTP client (raw sockets)")
    print()
    print("Usage:")
    print("  go2web -u <URL>          Make an HTTP request to the specified URL and print the response")
    print("  go2web -s <search-term>  Search the term using Google and print top 10 results")
    print("  go2web -h                Show this help")
    print()
    print("Examples:")
    print("  go2web -u https://example.com")
    print('  go2web -s "python programming"')
    print("  go2web -u https://jsonplaceholder.typicode.com/posts/1")


def fetch_url(url):
    """Fetch a URL and print human-readable response."""
    print(f"Fetching: {url}")
    print()

    try:
        response = http_request(url)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if response.status_code >= 400:
        print(f"HTTP Error {response.status_code}")
        print()

    text, links = format_response(response)
    print(text)

    if links:
        print()
        print("Links:")
        for i, (text, href) in enumerate(links, 1):
            print(f"  [{i}] {text} -> {href}")


def main():
    parser = argparse.ArgumentParser(
        prog="go2web",
        description="A command-line HTTP client built on raw TCP sockets.",
        add_help=False,
    )
    parser.add_argument("-u", type=str, help="URL to fetch")
    parser.add_argument("-s", nargs="+", help="Search term(s)")
    parser.add_argument("-h", "--help", action="store_true", help="Show help")

    args = parser.parse_args()

    if args.help or (not args.u and not args.s):
        print_help()
        sys.exit(0)

    if args.u:
        fetch_url(args.u)

    if args.s:
        search_term = " ".join(args.s)
        print(f"[TODO] Searching for: {search_term}")


if __name__ == "__main__":
    main()
