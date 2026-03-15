"""
go2web - A command-line HTTP client built on raw TCP sockets.
No HTTP libraries used - all requests are made via socket + ssl.
"""

import sys
import argparse

from http_client import http_request
from html_parser import format_response
from search import search_duckduckgo, format_search_results


def print_help():
    """Print usage help."""
    print("go2web - A command-line HTTP client (raw sockets)")
    print()
    print("Usage:")
    print("  go2web -u <URL>          Make an HTTP request to the specified URL and print the response")
    print("  go2web -s <search-term>  Search the term using DuckDuckGo and print top 10 results")
    print("  go2web -h                Show this help")
    print("  go2web --clear-cache     Clear the HTTP cache")
    print()
    print("Features:")
    print("  - HTTP/HTTPS via raw TCP sockets (no HTTP libraries)")
    print("  - Automatic redirect following")
    print("  - HTTP caching (Cache-Control, ETag, Last-Modified)")
    print("  - Content negotiation (HTML + JSON)")
    print("  - Human-readable output (HTML stripped, JSON pretty-printed)")
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
        for i, (link_text, href) in enumerate(links, 1):
            print(f"  [{i}] {link_text} -> {href}")


def search(query):
    """Search and display results, with option to open a result."""
    print(f'Searching for: "{query}"')
    print()

    try:
        results = search_duckduckgo(query)
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No results found.")
        return

    print(format_search_results(results))

    # Allow user to access a result
    while True:
        try:
            choice = input("Enter result number to open (or 'q' to quit): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice.lower() in ('q', 'quit', ''):
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                print()
                fetch_url(results[idx].url)
            else:
                print(f"Please enter a number between 1 and {len(results)}")
        except ValueError:
            print("Please enter a valid number or 'q' to quit")


def main():
    parser = argparse.ArgumentParser(
        prog="go2web",
        description="A command-line HTTP client built on raw TCP sockets.",
        add_help=False,
    )
    parser.add_argument("-u", type=str, help="URL to fetch")
    parser.add_argument("-s", nargs="+", help="Search term(s)")
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    parser.add_argument("--clear-cache", action="store_true", help="Clear HTTP cache")

    args = parser.parse_args()

    if args.clear_cache:
        from cache import clear_cache
        clear_cache()
        sys.exit(0)

    if args.help or (not args.u and not args.s):
        print_help()
        sys.exit(0)

    if args.u:
        fetch_url(args.u)

    if args.s:
        search_term = " ".join(args.s)
        search(search_term)


if __name__ == "__main__":
    main()
