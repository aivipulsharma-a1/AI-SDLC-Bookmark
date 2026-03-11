import urllib.parse

import requests
from bs4 import BeautifulSoup

_ALLOWED_SCHEMES = {"http", "https"}


def fetch_page_title(url: str, timeout: int = 5) -> str:
    """Attempt to fetch the HTML <title> of a URL.  Returns an empty string on failure.

    Only http and https URLs are fetched to prevent SSRF via non-web schemes.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
            return ""
        headers = {"User-Agent": "BookmarkManager/1.0"}
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("title")
        return tag.get_text(strip=True) if tag else ""
    except Exception:
        return ""
