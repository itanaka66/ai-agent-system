"""
Web Crawler Client
Fetches a URL and extracts text/links/metadata from its HTML - used as a
workflow node (CRAWLER_AGENT, see core/workflow_engine.py) and a standalone
REST endpoint (api_v1/crawler.py) for pulling external web content into an
agent pipeline.
"""

import asyncio
from typing import Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_USER_AGENT = "AI-Agent-System-Crawler/1.0"


class CrawlerClient:
    def __init__(self, timeout: int = 30, max_links: int = 100):
        self.timeout = timeout
        self.max_links = max_links

    async def fetch_page(self, url: str, headers: Optional[Dict] = None) -> Dict:
        """Fetch a URL. Returns {url, status, content, headers} or
        {url, status: "error", error} on failure - never raises."""

        request_headers = headers or {"User-Agent": DEFAULT_USER_AGENT}

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=request_headers) as response:
                    text = await response.text()
                    return {
                        "url": url,
                        "status": response.status,
                        "content": text,
                        "headers": dict(response.headers),
                    }
        except asyncio.TimeoutError:
            return {"url": url, "status": "error", "error": f"Timed out after {self.timeout}s"}
        except Exception as e:
            logger.error(f"Crawler fetch_page failed for {url}: {e}")
            return {"url": url, "status": "error", "error": str(e)}

    def extract_text(self, html: str, selector: str = "body") -> Dict:
        """Extract text from elements matching a CSS selector."""

        try:
            soup = BeautifulSoup(html, "html.parser")
            elements = soup.select(selector)

            return {
                "selector": selector,
                "count": len(elements),
                "texts": [elem.get_text(strip=True) for elem in elements],
            }
        except Exception as e:
            return {"selector": selector, "status": "error", "error": str(e)}

    def extract_links(self, html: str, base_url: str = "") -> Dict:
        """Extract <a href> links, resolved against base_url."""

        try:
            soup = BeautifulSoup(html, "html.parser")
            links: List[Dict] = []

            for a in soup.find_all("a", href=True):
                href = a["href"]
                absolute_url = urljoin(base_url, href) if base_url else href
                links.append({"url": absolute_url, "text": a.get_text(strip=True)})

            return {"count": len(links), "links": links[: self.max_links]}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def extract_metadata(self, html: str) -> Dict:
        """Extract <title>/description/OpenGraph metadata."""

        try:
            soup = BeautifulSoup(html, "html.parser")

            metadata = {
                "title": soup.title.string if soup.title else None,
                "description": None,
                "og_image": None,
                "og_type": None,
            }

            for meta in soup.find_all("meta"):
                name = (meta.get("name") or "").lower()
                property_ = (meta.get("property") or "").lower()
                content = meta.get("content")

                if name == "description":
                    metadata["description"] = content
                elif property_ == "og:image":
                    metadata["og_image"] = content
                elif property_ == "og:type":
                    metadata["og_type"] = content

            return metadata
        except Exception as e:
            return {"status": "error", "error": str(e)}
