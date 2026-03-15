"""
go2web - A command-line HTTP client built on raw TCP sockets.
No HTTP libraries used - all requests are made via socket + ssl.
"""

import sys
import argparse


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
        print(f"[TODO] Fetching URL: {args.u}")

    if args.s:
        search_term = " ".join(args.s)
        print(f"[TODO] Searching for: {search_term}")


if __name__ == "__main__":
    main()
