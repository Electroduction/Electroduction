#!/usr/bin/env python3
"""
Data Gathering & Collection Toolkit
====================================

A comprehensive toolkit for data gathering, web scraping, and information collection.
Provides tools for extracting, parsing, and organizing data from various sources.

Author: Electroduction Security Team
Version: 1.0.0

Features:
---------
- Web Scraping: HTTP requests, HTML parsing, content extraction
- Data Parsing: JSON, XML, CSV, HTML parsing utilities
- Content Extraction: Text, links, images, metadata extraction
- Rate Limiting: Respectful scraping with throttling
- Data Cleaning: Text normalization, deduplication
- Export: Multiple output formats

Usage:
------
    from data_collector import DataCollector, HTMLParser, ContentExtractor

    # Fetch and parse a webpage
    collector = DataCollector()
    response = collector.fetch("https://example.com")

    # Extract content
    extractor = ContentExtractor()
    links = extractor.extract_links(html_content)

Note: Always respect robots.txt and website terms of service.
"""

import re
import json
import csv
import hashlib
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
from io import StringIO
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set, Callable, Iterator
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from html.parser import HTMLParser as BaseHTMLParser
import xml.etree.ElementTree as ET


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class HTTPResponse:
    """Represents an HTTP response."""
    url: str
    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    encoding: str
    elapsed_ms: float
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def ok(self) -> bool:
        """Check if request was successful (2xx status)."""
        return 200 <= self.status_code < 300

    @property
    def json(self) -> Any:
        """Parse response as JSON."""
        return json.loads(self.text)


@dataclass
class ExtractedLink:
    """Represents an extracted link."""
    url: str
    text: str
    title: Optional[str]
    rel: Optional[str]
    is_external: bool
    is_anchor: bool


@dataclass
class ExtractedImage:
    """Represents an extracted image."""
    src: str
    alt: str
    title: Optional[str]
    width: Optional[int]
    height: Optional[int]


@dataclass
class ExtractedMetadata:
    """Represents extracted page metadata."""
    title: Optional[str]
    description: Optional[str]
    keywords: List[str]
    author: Optional[str]
    canonical_url: Optional[str]
    og_tags: Dict[str, str]
    twitter_tags: Dict[str, str]


@dataclass
class ScrapedPage:
    """Complete scraped page data."""
    url: str
    response: HTTPResponse
    metadata: ExtractedMetadata
    links: List[ExtractedLink]
    images: List[ExtractedImage]
    text_content: str
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# HTTP CLIENT
# =============================================================================

class HTTPClient:
    """
    Simple HTTP client for making requests.

    Supports:
    - GET and POST requests
    - Custom headers
    - Timeout handling
    - SSL verification
    - Basic authentication

    Example:
        >>> client = HTTPClient()
        >>> response = client.get("https://example.com")
        >>> print(response.status_code)
    """

    DEFAULT_HEADERS = {
        'User-Agent': 'DataCollector/1.0 (Educational/Research)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'identity',
        'Connection': 'keep-alive',
    }

    def __init__(self, timeout: float = 30.0, verify_ssl: bool = True):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.headers = dict(self.DEFAULT_HEADERS)

        # Create SSL context
        if not verify_ssl:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        else:
            self.ssl_context = ssl.create_default_context()

    def get(self, url: str, headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, str]] = None) -> HTTPResponse:
        """
        Make a GET request.

        Args:
            url: URL to request
            headers: Optional additional headers
            params: Optional query parameters

        Returns:
            HTTPResponse object
        """
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}" if '?' not in url else f"{url}&{query_string}"

        return self._request('GET', url, headers=headers)

    def post(self, url: str, data: Optional[Dict[str, Any]] = None,
             json_data: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None) -> HTTPResponse:
        """
        Make a POST request.

        Args:
            url: URL to request
            data: Form data to send
            json_data: JSON data to send
            headers: Optional additional headers

        Returns:
            HTTPResponse object
        """
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)

        body = None
        if json_data:
            body = json.dumps(json_data).encode('utf-8')
            request_headers['Content-Type'] = 'application/json'
        elif data:
            body = urllib.parse.urlencode(data).encode('utf-8')
            request_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        return self._request('POST', url, headers=request_headers, body=body)

    def _request(self, method: str, url: str,
                 headers: Optional[Dict[str, str]] = None,
                 body: Optional[bytes] = None) -> HTTPResponse:
        """Internal method to make HTTP requests."""
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)

        start_time = time.time()

        try:
            request = urllib.request.Request(
                url,
                data=body,
                headers=request_headers,
                method=method
            )

            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
                context=self.ssl_context
            ) as response:
                content = response.read()
                elapsed_ms = (time.time() - start_time) * 1000

                # Determine encoding
                encoding = response.headers.get_content_charset() or 'utf-8'
                try:
                    text = content.decode(encoding)
                except UnicodeDecodeError:
                    text = content.decode('utf-8', errors='replace')

                return HTTPResponse(
                    url=response.geturl(),
                    status_code=response.status,
                    headers=dict(response.headers),
                    content=content,
                    text=text,
                    encoding=encoding,
                    elapsed_ms=elapsed_ms
                )

        except urllib.error.HTTPError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            content = e.read() if hasattr(e, 'read') else b''
            return HTTPResponse(
                url=url,
                status_code=e.code,
                headers=dict(e.headers) if hasattr(e, 'headers') else {},
                content=content,
                text=content.decode('utf-8', errors='replace'),
                encoding='utf-8',
                elapsed_ms=elapsed_ms
            )

        except urllib.error.URLError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return HTTPResponse(
                url=url,
                status_code=0,
                headers={},
                content=b'',
                text=f"Error: {e.reason}",
                encoding='utf-8',
                elapsed_ms=elapsed_ms
            )


# =============================================================================
# HTML PARSER
# =============================================================================

class HTMLParserImpl(BaseHTMLParser):
    """Internal HTML parser implementation."""

    def __init__(self):
        super().__init__()
        self.tags = []
        self.current_tag = None
        self.current_attrs = {}
        self.text_content = []
        self.in_script = False
        self.in_style = False

        # Extracted data
        self.title = None
        self.meta_tags = []
        self.links = []
        self.images = []
        self.headings = []
        self.forms = []
        self.scripts = []
        self.styles = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        attrs_dict = dict(attrs)
        self.current_tag = tag
        self.current_attrs = attrs_dict

        self.tags.append({'tag': tag, 'attrs': attrs_dict, 'type': 'start'})

        if tag == 'script':
            self.in_script = True
        elif tag == 'style':
            self.in_style = True
        elif tag == 'meta':
            self.meta_tags.append(attrs_dict)
        elif tag == 'a':
            self.links.append(attrs_dict)
        elif tag == 'img':
            self.images.append(attrs_dict)
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.headings.append({'level': int(tag[1]), 'attrs': attrs_dict, 'text': ''})
        elif tag == 'form':
            self.forms.append(attrs_dict)
        elif tag == 'link':
            if attrs_dict.get('rel') == 'stylesheet':
                self.styles.append(attrs_dict.get('href', ''))

    def handle_endtag(self, tag: str):
        if tag == 'script':
            self.in_script = False
        elif tag == 'style':
            self.in_style = False
        self.current_tag = None

    def handle_data(self, data: str):
        if self.in_script:
            self.scripts.append(data)
        elif self.in_style:
            pass  # Ignore CSS
        else:
            text = data.strip()
            if text:
                self.text_content.append(text)
                if self.current_tag == 'title':
                    self.title = text
                elif self.current_tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6') and self.headings:
                    self.headings[-1]['text'] = text


class HTMLParser:
    """
    HTML parsing utilities.

    Provides:
    - DOM-like parsing
    - Element extraction
    - Text extraction
    - Attribute extraction

    Example:
        >>> parser = HTMLParser()
        >>> result = parser.parse(html_content)
        >>> print(result['title'])
    """

    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parse HTML content and extract structure.

        Args:
            html: HTML string to parse

        Returns:
            Dictionary with extracted data
        """
        parser = HTMLParserImpl()

        try:
            parser.feed(html)
        except Exception:
            pass  # Continue with partial results

        return {
            'title': parser.title,
            'meta_tags': parser.meta_tags,
            'links': parser.links,
            'images': parser.images,
            'headings': parser.headings,
            'forms': parser.forms,
            'scripts': len(parser.scripts),
            'text_content': ' '.join(parser.text_content)
        }

    def extract_text(self, html: str, preserve_structure: bool = False) -> str:
        """
        Extract text content from HTML.

        Args:
            html: HTML string
            preserve_structure: Whether to preserve some formatting

        Returns:
            Extracted text
        """
        # Remove script and style elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Replace block elements with newlines
        if preserve_structure:
            html = re.sub(r'</(p|div|br|h[1-6]|li|tr)>', '\n', html, flags=re.IGNORECASE)
            html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)

        # Remove all tags
        text = re.sub(r'<[^>]+>', ' ', html)

        # Decode HTML entities
        text = self._decode_entities(text)

        # Clean whitespace
        if preserve_structure:
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
        else:
            text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _decode_entities(self, text: str) -> str:
        """Decode common HTML entities."""
        entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&apos;': "'",
            '&copy;': '©',
            '&reg;': '®',
            '&trade;': '™',
            '&mdash;': '—',
            '&ndash;': '–',
            '&hellip;': '…',
        }

        for entity, char in entities.items():
            text = text.replace(entity, char)

        # Numeric entities
        text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
        text = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), text)

        return text

    def find_elements(self, html: str, tag: str, attrs: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Find elements by tag name and attributes.

        Args:
            html: HTML string
            tag: Tag name to search for
            attrs: Optional attribute filters

        Returns:
            List of matching elements
        """
        # Build pattern
        pattern = f'<{tag}'
        if attrs:
            for key, value in attrs.items():
                pattern += f'[^>]*{key}=["\']?{re.escape(value)}["\']?'
        pattern += r'[^>]*>(.*?)</' + tag + '>'

        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

        elements = []
        for match in matches:
            elements.append({
                'tag': tag,
                'content': match,
                'text': self.extract_text(match)
            })

        return elements


# =============================================================================
# CONTENT EXTRACTOR
# =============================================================================

class ContentExtractor:
    """
    Extract specific content from web pages.

    Supports extraction of:
    - Links and URLs
    - Images
    - Metadata (title, description, OG tags)
    - Structured data
    - Text content

    Example:
        >>> extractor = ContentExtractor()
        >>> links = extractor.extract_links(html, base_url="https://example.com")
        >>> images = extractor.extract_images(html)
    """

    def __init__(self):
        """Initialize content extractor."""
        self.html_parser = HTMLParser()

    def extract_links(self, html: str, base_url: Optional[str] = None) -> List[ExtractedLink]:
        """
        Extract all links from HTML.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of ExtractedLink objects
        """
        links = []

        # Pattern for anchor tags
        pattern = r'<a\s+([^>]*)>(.*?)</a>'

        for match in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
            attrs_str = match.group(1)
            text = self.html_parser.extract_text(match.group(2))

            # Extract href
            href_match = re.search(r'href=["\']([^"\']+)["\']', attrs_str)
            if not href_match:
                continue

            href = href_match.group(1)

            # Extract other attributes
            title_match = re.search(r'title=["\']([^"\']+)["\']', attrs_str)
            rel_match = re.search(r'rel=["\']([^"\']+)["\']', attrs_str)

            # Resolve relative URLs
            if base_url and not href.startswith(('http://', 'https://', '//')):
                href = urllib.parse.urljoin(base_url, href)

            # Determine if external
            is_external = False
            is_anchor = href.startswith('#')

            if base_url and not is_anchor:
                base_domain = urllib.parse.urlparse(base_url).netloc
                link_domain = urllib.parse.urlparse(href).netloc
                is_external = link_domain and link_domain != base_domain

            links.append(ExtractedLink(
                url=href,
                text=text.strip(),
                title=title_match.group(1) if title_match else None,
                rel=rel_match.group(1) if rel_match else None,
                is_external=is_external,
                is_anchor=is_anchor
            ))

        return links

    def extract_images(self, html: str, base_url: Optional[str] = None) -> List[ExtractedImage]:
        """
        Extract all images from HTML.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative URLs

        Returns:
            List of ExtractedImage objects
        """
        images = []

        # Pattern for img tags
        pattern = r'<img\s+([^>]+)/?>'

        for match in re.finditer(pattern, html, re.IGNORECASE):
            attrs_str = match.group(1)

            # Extract src
            src_match = re.search(r'src=["\']([^"\']+)["\']', attrs_str)
            if not src_match:
                continue

            src = src_match.group(1)

            # Resolve relative URLs
            if base_url and not src.startswith(('http://', 'https://', '//', 'data:')):
                src = urllib.parse.urljoin(base_url, src)

            # Extract other attributes
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', attrs_str)
            title_match = re.search(r'title=["\']([^"\']+)["\']', attrs_str)
            width_match = re.search(r'width=["\']?(\d+)["\']?', attrs_str)
            height_match = re.search(r'height=["\']?(\d+)["\']?', attrs_str)

            images.append(ExtractedImage(
                src=src,
                alt=alt_match.group(1) if alt_match else '',
                title=title_match.group(1) if title_match else None,
                width=int(width_match.group(1)) if width_match else None,
                height=int(height_match.group(1)) if height_match else None
            ))

        return images

    def extract_metadata(self, html: str) -> ExtractedMetadata:
        """
        Extract page metadata.

        Args:
            html: HTML content

        Returns:
            ExtractedMetadata object
        """
        # Title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
        title = self.html_parser.extract_text(title_match.group(1)) if title_match else None

        # Meta tags
        description = None
        keywords = []
        author = None
        canonical = None
        og_tags = {}
        twitter_tags = {}

        meta_pattern = r'<meta\s+([^>]+)/?>'

        for match in re.finditer(meta_pattern, html, re.IGNORECASE):
            attrs_str = match.group(1)

            # Get name/property and content
            name_match = re.search(r'name=["\']([^"\']+)["\']', attrs_str)
            property_match = re.search(r'property=["\']([^"\']+)["\']', attrs_str)
            content_match = re.search(r'content=["\']([^"\']*)["\']', attrs_str)

            if not content_match:
                continue

            content = content_match.group(1)

            if name_match:
                name = name_match.group(1).lower()
                if name == 'description':
                    description = content
                elif name == 'keywords':
                    keywords = [k.strip() for k in content.split(',')]
                elif name == 'author':
                    author = content
                elif name.startswith('twitter:'):
                    twitter_tags[name[8:]] = content

            if property_match:
                prop = property_match.group(1).lower()
                if prop.startswith('og:'):
                    og_tags[prop[3:]] = content

        # Canonical URL
        canonical_match = re.search(
            r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if canonical_match:
            canonical = canonical_match.group(1)

        return ExtractedMetadata(
            title=title,
            description=description,
            keywords=keywords,
            author=author,
            canonical_url=canonical,
            og_tags=og_tags,
            twitter_tags=twitter_tags
        )

    def extract_tables(self, html: str) -> List[List[List[str]]]:
        """
        Extract tables from HTML.

        Returns:
            List of tables, each as a list of rows, each row as list of cells
        """
        tables = []

        table_pattern = r'<table[^>]*>(.*?)</table>'

        for table_match in re.finditer(table_pattern, html, re.DOTALL | re.IGNORECASE):
            table_html = table_match.group(1)
            rows = []

            # Find all rows
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            for row_match in re.finditer(row_pattern, table_html, re.DOTALL | re.IGNORECASE):
                row_html = row_match.group(1)
                cells = []

                # Find all cells (th or td)
                cell_pattern = r'<t[hd][^>]*>(.*?)</t[hd]>'
                for cell_match in re.finditer(cell_pattern, row_html, re.DOTALL | re.IGNORECASE):
                    cell_text = self.html_parser.extract_text(cell_match.group(1))
                    cells.append(cell_text)

                if cells:
                    rows.append(cells)

            if rows:
                tables.append(rows)

        return tables

    def extract_json_ld(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract JSON-LD structured data from HTML.

        Returns:
            List of parsed JSON-LD objects
        """
        json_ld_data = []

        pattern = r'<script\s+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'

        for match in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
            try:
                data = json.loads(match.group(1))
                json_ld_data.append(data)
            except json.JSONDecodeError:
                pass

        return json_ld_data


# =============================================================================
# DATA PARSERS
# =============================================================================

class DataParser:
    """
    Parse various data formats.

    Supports:
    - JSON
    - XML
    - CSV
    - INI-style configs

    Example:
        >>> parser = DataParser()
        >>> data = parser.parse_json('{"key": "value"}')
        >>> xml_data = parser.parse_xml('<root><item>value</item></root>')
    """

    def parse_json(self, content: str) -> Any:
        """Parse JSON content."""
        return json.loads(content)

    def parse_xml(self, content: str) -> Dict[str, Any]:
        """
        Parse XML content to dictionary.

        Args:
            content: XML string

        Returns:
            Dictionary representation of XML
        """
        try:
            root = ET.fromstring(content)
            return self._xml_to_dict(root)
        except ET.ParseError as e:
            return {'error': str(e)}

    def _xml_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to dictionary recursively."""
        result = {}

        # Add attributes
        if element.attrib:
            result['@attributes'] = dict(element.attrib)

        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['#text'] = element.text.strip()

        # Add children
        for child in element:
            child_data = self._xml_to_dict(child)

            if child.tag in result:
                # Convert to list if multiple children with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        return result if result else (element.text.strip() if element.text else '')

    def parse_csv(self, content: str, delimiter: str = ',',
                  has_header: bool = True) -> List[Dict[str, Any]]:
        """
        Parse CSV content.

        Args:
            content: CSV string
            delimiter: Field delimiter
            has_header: Whether first row is header

        Returns:
            List of dictionaries (if has_header) or list of lists
        """
        reader = csv.reader(StringIO(content), delimiter=delimiter)
        rows = list(reader)

        if not rows:
            return []

        if has_header:
            headers = rows[0]
            return [
                dict(zip(headers, row))
                for row in rows[1:]
            ]
        else:
            return rows

    def parse_key_value(self, content: str, delimiter: str = '=',
                        comment_char: str = '#') -> Dict[str, str]:
        """
        Parse key-value format (like INI without sections).

        Args:
            content: Content string
            delimiter: Key-value delimiter
            comment_char: Comment character

        Returns:
            Dictionary of key-value pairs
        """
        result = {}

        for line in content.split('\n'):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith(comment_char):
                continue

            if delimiter in line:
                key, value = line.split(delimiter, 1)
                result[key.strip()] = value.strip()

        return result


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """
    Rate limiter for respectful scraping.

    Implements token bucket algorithm with support for:
    - Per-domain rate limits
    - Global rate limits
    - Burst allowance

    Example:
        >>> limiter = RateLimiter(requests_per_second=1.0)
        >>> limiter.wait("example.com")  # Blocks if needed
        >>> # ... make request ...
    """

    def __init__(self, requests_per_second: float = 1.0, burst: int = 5):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum sustained request rate
            burst: Maximum burst size
        """
        self.rate = requests_per_second
        self.burst = burst
        self.tokens: Dict[str, float] = {}
        self.last_update: Dict[str, float] = {}

    def wait(self, domain: str = '_global'):
        """
        Wait until a request is allowed.

        Args:
            domain: Domain to rate limit (or '_global' for global limit)
        """
        now = time.time()

        if domain not in self.tokens:
            self.tokens[domain] = self.burst
            self.last_update[domain] = now

        # Add tokens based on elapsed time
        elapsed = now - self.last_update[domain]
        self.tokens[domain] = min(
            self.burst,
            self.tokens[domain] + elapsed * self.rate
        )
        self.last_update[domain] = now

        # Wait if no tokens available
        if self.tokens[domain] < 1:
            wait_time = (1 - self.tokens[domain]) / self.rate
            time.sleep(wait_time)
            self.tokens[domain] = 0
        else:
            self.tokens[domain] -= 1

    def can_request(self, domain: str = '_global') -> bool:
        """Check if a request is currently allowed without waiting."""
        now = time.time()

        if domain not in self.tokens:
            return True

        elapsed = now - self.last_update[domain]
        available = min(
            self.burst,
            self.tokens[domain] + elapsed * self.rate
        )

        return available >= 1


# =============================================================================
# DATA CLEANER
# =============================================================================

class DataCleaner:
    """
    Clean and normalize collected data.

    Provides:
    - Text normalization
    - Whitespace cleanup
    - Unicode normalization
    - Deduplication

    Example:
        >>> cleaner = DataCleaner()
        >>> clean_text = cleaner.clean_text("  Hello   World  ")
        >>> unique_items = cleaner.deduplicate(items)
    """

    def clean_text(self, text: str, normalize_whitespace: bool = True,
                   remove_control_chars: bool = True,
                   lowercase: bool = False) -> str:
        """
        Clean and normalize text.

        Args:
            text: Input text
            normalize_whitespace: Collapse multiple spaces
            remove_control_chars: Remove control characters
            lowercase: Convert to lowercase

        Returns:
            Cleaned text
        """
        if remove_control_chars:
            # Remove control characters except newline and tab
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

        if normalize_whitespace:
            # Normalize various whitespace to single space
            text = re.sub(r'[\t\f\v]+', ' ', text)
            text = re.sub(r' +', ' ', text)
            text = re.sub(r'\n +', '\n', text)
            text = re.sub(r' +\n', '\n', text)
            text = text.strip()

        if lowercase:
            text = text.lower()

        return text

    def normalize_url(self, url: str) -> str:
        """
        Normalize a URL for comparison.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        parsed = urllib.parse.urlparse(url)

        # Lowercase scheme and host
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove default ports
        if netloc.endswith(':80') and scheme == 'http':
            netloc = netloc[:-3]
        elif netloc.endswith(':443') and scheme == 'https':
            netloc = netloc[:-4]

        # Normalize path
        path = parsed.path or '/'

        # Sort query parameters
        query = urllib.parse.urlencode(
            sorted(urllib.parse.parse_qsl(parsed.query))
        )

        # Rebuild URL
        return urllib.parse.urlunparse((
            scheme, netloc, path, '', query, ''
        ))

    def deduplicate(self, items: List[Any], key: Optional[Callable] = None) -> List[Any]:
        """
        Remove duplicates while preserving order.

        Args:
            items: List of items
            key: Optional function to extract comparison key

        Returns:
            Deduplicated list
        """
        seen = set()
        result = []

        for item in items:
            k = key(item) if key else item

            # Handle unhashable types
            if isinstance(k, (list, dict)):
                k = json.dumps(k, sort_keys=True)

            if k not in seen:
                seen.add(k)
                result.append(item)

        return result

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower()


# =============================================================================
# DATA EXPORTER
# =============================================================================

class DataExporter:
    """
    Export collected data to various formats.

    Supports:
    - JSON
    - CSV
    - Markdown
    - Plain text

    Example:
        >>> exporter = DataExporter()
        >>> exporter.to_json(data, "output.json")
        >>> csv_string = exporter.to_csv(data)
    """

    def to_json(self, data: Any, filepath: Optional[str] = None,
                indent: int = 2) -> str:
        """
        Export data to JSON.

        Args:
            data: Data to export
            filepath: Optional file path to save
            indent: JSON indentation

        Returns:
            JSON string
        """
        json_str = json.dumps(data, indent=indent, default=str)

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def to_csv(self, data: List[Dict[str, Any]], filepath: Optional[str] = None) -> str:
        """
        Export data to CSV.

        Args:
            data: List of dictionaries
            filepath: Optional file path to save

        Returns:
            CSV string
        """
        if not data:
            return ""

        output = StringIO()

        # Get all keys for headers
        headers = list(OrderedDict.fromkeys(
            key for item in data for key in item.keys()
        ))

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

        csv_str = output.getvalue()

        if filepath:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_str)

        return csv_str

    def to_markdown(self, data: List[Dict[str, Any]], title: str = "Data Export") -> str:
        """
        Export data to Markdown table.

        Args:
            data: List of dictionaries
            title: Table title

        Returns:
            Markdown string
        """
        if not data:
            return f"# {title}\n\nNo data."

        headers = list(data[0].keys())

        lines = [f"# {title}\n"]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")

        for item in data:
            row = [str(item.get(h, '')).replace('|', '\\|') for h in headers]
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)


# =============================================================================
# MAIN DATA COLLECTOR CLASS
# =============================================================================

class DataCollector:
    """
    Main class combining all data collection capabilities.

    Provides a unified interface for:
    - Fetching web content
    - Parsing HTML/JSON/XML
    - Extracting specific content
    - Cleaning and exporting data

    Example:
        >>> collector = DataCollector()
        >>>
        >>> # Fetch and parse a page
        >>> page = collector.scrape_page("https://example.com")
        >>> print(page.metadata.title)
        >>>
        >>> # Export collected data
        >>> collector.export_data(pages, "output.json")
    """

    def __init__(self, rate_limit: float = 1.0, timeout: float = 30.0):
        """
        Initialize data collector.

        Args:
            rate_limit: Requests per second limit
            timeout: HTTP request timeout
        """
        self.client = HTTPClient(timeout=timeout)
        self.parser = HTMLParser()
        self.extractor = ContentExtractor()
        self.data_parser = DataParser()
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.cleaner = DataCleaner()
        self.exporter = DataExporter()

    def fetch(self, url: str, respect_rate_limit: bool = True) -> HTTPResponse:
        """
        Fetch a URL.

        Args:
            url: URL to fetch
            respect_rate_limit: Whether to apply rate limiting

        Returns:
            HTTPResponse object
        """
        if respect_rate_limit:
            domain = self.cleaner.extract_domain(url)
            self.rate_limiter.wait(domain)

        return self.client.get(url)

    def scrape_page(self, url: str) -> Optional[ScrapedPage]:
        """
        Scrape a complete page.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage object or None if failed
        """
        response = self.fetch(url)

        if not response.ok:
            return None

        html = response.text

        metadata = self.extractor.extract_metadata(html)
        links = self.extractor.extract_links(html, base_url=url)
        images = self.extractor.extract_images(html, base_url=url)
        text_content = self.parser.extract_text(html, preserve_structure=True)

        return ScrapedPage(
            url=url,
            response=response,
            metadata=metadata,
            links=links,
            images=images,
            text_content=text_content
        )

    def fetch_json(self, url: str) -> Optional[Any]:
        """
        Fetch and parse JSON from URL.

        Args:
            url: URL to fetch

        Returns:
            Parsed JSON or None if failed
        """
        response = self.fetch(url)

        if not response.ok:
            return None

        try:
            return response.json
        except json.JSONDecodeError:
            return None

    def extract_data(self, html: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract all available data from HTML.

        Args:
            html: HTML content
            base_url: Base URL for resolving links

        Returns:
            Dictionary with all extracted data
        """
        return {
            'metadata': self.extractor.extract_metadata(html),
            'links': self.extractor.extract_links(html, base_url),
            'images': self.extractor.extract_images(html, base_url),
            'tables': self.extractor.extract_tables(html),
            'json_ld': self.extractor.extract_json_ld(html),
            'text': self.parser.extract_text(html)
        }

    def export_data(self, data: Any, filepath: str, format: str = 'json'):
        """
        Export collected data.

        Args:
            data: Data to export
            filepath: Output file path
            format: Output format (json, csv, markdown)
        """
        if format == 'json':
            self.exporter.to_json(data, filepath)
        elif format == 'csv':
            if isinstance(data, list):
                self.exporter.to_csv(data, filepath)
        elif format == 'markdown':
            if isinstance(data, list):
                md = self.exporter.to_markdown(data)
                with open(filepath, 'w') as f:
                    f.write(md)


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Command-line interface for the Data Collector."""
    print("=" * 60)
    print("DATA GATHERING & COLLECTION TOOLKIT")
    print("=" * 60)
    print()

    # Initialize collector
    collector = DataCollector(rate_limit=2.0)

    # Demo: HTTP Client
    print("1. HTTP CLIENT DEMO")
    print("-" * 40)

    client = collector.client
    print(f"Default User-Agent: {client.headers.get('User-Agent')}")
    print(f"Timeout: {client.timeout}s")
    print()

    # Demo: HTML Parsing
    print("2. HTML PARSING DEMO")
    print("-" * 40)

    sample_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample Page</title>
        <meta name="description" content="This is a sample page for testing">
        <meta name="keywords" content="test, sample, demo">
        <meta property="og:title" content="OG Title">
    </head>
    <body>
        <h1>Welcome</h1>
        <p>This is a paragraph with <a href="/link1" title="Link 1">a link</a>.</p>
        <p>Here's another <a href="https://external.com">external link</a>.</p>
        <img src="/images/test.jpg" alt="Test image" width="100" height="100">
        <table>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td>Item 1</td><td>100</td></tr>
            <tr><td>Item 2</td><td>200</td></tr>
        </table>
    </body>
    </html>
    '''

    parsed = collector.parser.parse(sample_html)
    print(f"Title: {parsed['title']}")
    print(f"Links found: {len(parsed['links'])}")
    print(f"Images found: {len(parsed['images'])}")
    print()

    # Demo: Metadata Extraction
    print("3. METADATA EXTRACTION DEMO")
    print("-" * 40)

    metadata = collector.extractor.extract_metadata(sample_html)
    print(f"Title: {metadata.title}")
    print(f"Description: {metadata.description}")
    print(f"Keywords: {metadata.keywords}")
    print(f"OG Tags: {metadata.og_tags}")
    print()

    # Demo: Link Extraction
    print("4. LINK EXTRACTION DEMO")
    print("-" * 40)

    links = collector.extractor.extract_links(sample_html, base_url="https://example.com")
    for link in links:
        print(f"  URL: {link.url}")
        print(f"  Text: {link.text}")
        print(f"  External: {link.is_external}")
        print()

    # Demo: Table Extraction
    print("5. TABLE EXTRACTION DEMO")
    print("-" * 40)

    tables = collector.extractor.extract_tables(sample_html)
    for i, table in enumerate(tables):
        print(f"Table {i+1}:")
        for row in table:
            print(f"  {row}")
    print()

    # Demo: Data Parsing
    print("6. DATA PARSING DEMO")
    print("-" * 40)

    # JSON
    json_data = '{"name": "John", "age": 30, "city": "New York"}'
    parsed_json = collector.data_parser.parse_json(json_data)
    print(f"JSON parsed: {parsed_json}")

    # CSV
    csv_data = "name,age,city\nJohn,30,New York\nJane,25,Boston"
    parsed_csv = collector.data_parser.parse_csv(csv_data)
    print(f"CSV parsed: {parsed_csv}")

    # XML
    xml_data = '<root><item id="1">Value 1</item><item id="2">Value 2</item></root>'
    parsed_xml = collector.data_parser.parse_xml(xml_data)
    print(f"XML parsed: {parsed_xml}")
    print()

    # Demo: Data Cleaning
    print("7. DATA CLEANING DEMO")
    print("-" * 40)

    cleaner = collector.cleaner

    dirty_text = "  Hello   World  \n\n\n  Test  "
    clean_text = cleaner.clean_text(dirty_text)
    print(f"Original: {repr(dirty_text)}")
    print(f"Cleaned: {repr(clean_text)}")

    url1 = "HTTPS://Example.Com:443/path/?b=2&a=1"
    normalized = cleaner.normalize_url(url1)
    print(f"URL normalized: {normalized}")

    items = [1, 2, 2, 3, 3, 3, 4]
    unique = cleaner.deduplicate(items)
    print(f"Deduplicated: {unique}")
    print()

    # Demo: Data Export
    print("8. DATA EXPORT DEMO")
    print("-" * 40)

    export_data = [
        {'name': 'Alice', 'age': 30, 'role': 'Engineer'},
        {'name': 'Bob', 'age': 25, 'role': 'Designer'},
    ]

    exporter = collector.exporter
    json_output = exporter.to_json(export_data)
    print("JSON output:")
    print(json_output[:100] + "...")

    csv_output = exporter.to_csv(export_data)
    print("\nCSV output:")
    print(csv_output)

    md_output = exporter.to_markdown(export_data, "Sample Data")
    print("Markdown output:")
    print(md_output[:200] + "...")
    print()

    # Demo: Rate Limiter
    print("9. RATE LIMITER DEMO")
    print("-" * 40)

    limiter = RateLimiter(requests_per_second=2.0, burst=3)
    print(f"Rate: {limiter.rate} req/s, Burst: {limiter.burst}")

    for i in range(5):
        can_request = limiter.can_request("test.com")
        print(f"Request {i+1}: Can request = {can_request}")
        if can_request:
            limiter.wait("test.com")
    print()

    print("=" * 60)
    print("Data Gathering Toolkit Demo Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
