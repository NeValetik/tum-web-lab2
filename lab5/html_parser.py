"""
HTML to text converter using Python's built-in html.parser.
Strips HTML tags and presents human-readable content.
"""

from html.parser import HTMLParser
from html import unescape
import json


class HTMLToTextParser(HTMLParser):
    """Convert HTML to human-readable plain text."""

    BLOCK_TAGS = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6",
                  "li", "tr", "blockquote", "pre", "hr", "section", "article",
                  "header", "footer", "nav", "main", "aside", "dt", "dd"}
    SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "meta", "link"}
    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self):
        super().__init__()
        self.result = []
        self.skip_depth = 0
        self.current_tag = None
        self.links = []
        self.in_link = False
        self.link_text = []
        self.link_href = ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        self.current_tag = tag

        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        if tag in self.BLOCK_TAGS:
            self.result.append("\n")

        if tag in self.HEADING_TAGS:
            self.result.append("\n")

        if tag == "hr":
            self.result.append("\n" + "-" * 40 + "\n")

        if tag == "li":
            self.result.append("  * ")

        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if href and href.startswith("http"):
                self.in_link = True
                self.link_href = href
                self.link_text = []

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in self.SKIP_TAGS:
            self.skip_depth -= 1
            return

        if self.skip_depth > 0:
            return

        if tag in self.HEADING_TAGS:
            self.result.append("\n")

        if tag == "a" and self.in_link:
            text = "".join(self.link_text).strip()
            if text and self.link_href:
                self.links.append((text, self.link_href))
                self.result.append(f" [{len(self.links)}]")
            self.in_link = False
            self.link_href = ""
            self.link_text = []

        if tag == "br":
            self.result.append("\n")

    def handle_data(self, data):
        if self.skip_depth > 0:
            return

        text = data
        if self.in_link:
            self.link_text.append(text)

        self.result.append(text)

    def handle_entityref(self, name):
        self.handle_data(unescape(f"&{name};"))

    def handle_charref(self, name):
        self.handle_data(unescape(f"&#{name};"))

    def get_text(self):
        raw = "".join(self.result)
        # Clean up excessive whitespace
        lines = raw.split("\n")
        cleaned = []
        prev_blank = False
        for line in lines:
            stripped = " ".join(line.split())
            if not stripped:
                if not prev_blank:
                    cleaned.append("")
                    prev_blank = True
            else:
                cleaned.append(stripped)
                prev_blank = False
        return "\n".join(cleaned).strip()

    def get_links(self):
        return self.links


def html_to_text(html_content):
    """Convert HTML string to human-readable text. Returns (text, links)."""
    parser = HTMLToTextParser()
    parser.feed(html_content)
    return parser.get_text(), parser.get_links()


def format_json(json_str):
    """Pretty-print JSON string."""
    try:
        data = json.loads(json_str)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return json_str


def format_response(response):
    """Format an HttpResponse into human-readable text. Returns (text, links)."""
    if response.is_json:
        return format_json(response.body), []
    elif response.is_html:
        return html_to_text(response.body)
    else:
        return response.body, []
