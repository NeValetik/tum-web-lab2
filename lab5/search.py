"""
Search engine integration using raw socket HTTP client.
Uses DuckDuckGo HTML version for search results.
"""

import re
from urllib.parse import quote, unquote
from http_client import http_request
from html_parser import html_to_text


class SearchResult:
    """A single search result."""

    def __init__(self, title, url, snippet=""):
        self.title = title
        self.url = url
        self.snippet = snippet

    def __str__(self):
        result = f"  {self.title}"
        result += f"\n  {self.url}"
        if self.snippet:
            result += f"\n  {self.snippet}"
        return result


def search_duckduckgo(query, num_results=10):
    """
    Search DuckDuckGo and return top results.
    Uses the HTML-only version of DuckDuckGo (lite.duckduckgo.com).
    """
    encoded_query = quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

    response = http_request(url)

    if response.status_code != 200:
        print(f"Search failed with HTTP {response.status_code}")
        return []

    return parse_duckduckgo_results(response.body, num_results)


def parse_duckduckgo_results(html_body, num_results=10):
    """Parse DuckDuckGo HTML results page."""
    results = []

    # DuckDuckGo HTML results have links in <a class="result__a" href="...">
    # and snippets in <a class="result__snippet" ...>

    # Extract result blocks - each result link has class "result__a"
    link_pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        re.DOTALL | re.IGNORECASE
    )

    snippet_pattern = re.compile(
        r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL | re.IGNORECASE
    )

    links = link_pattern.findall(html_body)
    snippets = snippet_pattern.findall(html_body)

    for i, (href, title_html) in enumerate(links):
        if len(results) >= num_results:
            break

        # Clean title
        title = re.sub(r'<[^>]+>', '', title_html).strip()
        title = re.sub(r'\s+', ' ', title)

        # Decode URL - DuckDuckGo wraps URLs in a redirect
        url = href
        if "uddg=" in url:
            url_match = re.search(r'uddg=([^&]+)', url)
            if url_match:
                url = unquote(url_match.group(1))
        elif url.startswith("//duckduckgo.com/l/?"):
            url_match = re.search(r'uddg=([^&]+)', url)
            if url_match:
                url = unquote(url_match.group(1))

        # Skip non-http results
        if not url.startswith("http"):
            continue

        # Clean snippet
        snippet = ""
        if i < len(snippets):
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            snippet = re.sub(r'\s+', ' ', snippet)

        results.append(SearchResult(title, url, snippet))

    return results


def format_search_results(results):
    """Format search results for display."""
    if not results:
        return "No results found."

    output = []
    for i, result in enumerate(results, 1):
        output.append(f"{i}. {result.title}")
        output.append(f"   {result.url}")
        if result.snippet:
            output.append(f"   {result.snippet}")
        output.append("")

    return "\n".join(output)
